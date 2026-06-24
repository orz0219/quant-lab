"""Roadmap / 待开发列表 API。"""
import json
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from app.core.config import settings
from app.core.database import DuckDBPool

router = APIRouter()
_db = DuckDBPool(settings.DB_PATH)


def _ensure_table() -> None:
    """确保 roadmap_items 表存在。"""
    _db.execute(
        """
        CREATE TABLE IF NOT EXISTS roadmap_items (
            id VARCHAR PRIMARY KEY,
            title VARCHAR NOT NULL,
            description VARCHAR DEFAULT '',
            status VARCHAR DEFAULT 'todo',
            priority VARCHAR DEFAULT 'medium',
            category VARCHAR DEFAULT 'feature',
            subtasks VARCHAR DEFAULT '[]',
            created_at VARCHAR DEFAULT '',
            updated_at VARCHAR DEFAULT ''
        )
        """
    )


def _row_to_dict(row: tuple) -> dict:
    return {
        'id': row[0],
        'title': row[1] or '',
        'description': row[2] or '',
        'status': row[3] or 'todo',
        'priority': row[4] or 'medium',
        'category': row[5] or 'feature',
        'subtasks': _parse_subtasks(row[6]),
        'created_at': row[7],
        'updated_at': row[8],
    }


def _parse_subtasks(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


@router.get("")
def list_items(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
):
    """返回待开发列表，支持按状态与关键词筛选。"""
    _ensure_table()
    sql = (
        "SELECT id, title, description, status, priority, category, subtasks, created_at, updated_at "
        "FROM roadmap_items WHERE 1=1"
    )
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    keyword = (search or "").strip()
    if keyword:
        sql += " AND (UPPER(title) LIKE UPPER(?) OR UPPER(description) LIKE UPPER(?))"
        like = f"%{keyword}%"
        params.extend([like, like])
    sql += " ORDER BY CASE status WHEN 'todo' THEN 0 WHEN 'doing' THEN 1 ELSE 2 END, created_at DESC LIMIT ?"
    params.append(limit)
    rows = _db.query_list(sql, params)
    items = [_row_to_dict(r) for r in rows]
    return {"total": len(items), "items": items}


@router.get("/{item_id}")
def get_item(item_id: str):
    """获取单个任务详情。"""
    _ensure_table()
    rows = _db.query_list(
        "SELECT id, title, description, status, priority, category, subtasks, created_at, updated_at "
        "FROM roadmap_items WHERE id = ?",
        [item_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _row_to_dict(rows[0])


@router.post("", status_code=201)
def create_item(body: dict):
    """创建新任务。"""
    _ensure_table()
    title = (body.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    item_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    subtasks = json.dumps(body.get("subtasks") or [], ensure_ascii=False)
    _db.execute(
        "INSERT INTO roadmap_items (id, title, description, status, priority, category, subtasks, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            item_id,
            title,
            body.get("description") or "",
            body.get("status") or "todo",
            body.get("priority") or "medium",
            body.get("category") or "feature",
            subtasks,
            now,
            now,
        ],
    )
    return {"id": item_id, "created_at": now}


@router.put("/{item_id}")
def update_item(item_id: str, body: dict):
    """更新任务（标题、描述、状态、优先级、分类、子任务）。"""
    _ensure_table()
    existing = _db.query_list("SELECT id FROM roadmap_items WHERE id = ?", [item_id])
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    now = datetime.utcnow().isoformat()
    subtasks = json.dumps(body.get("subtasks") or [], ensure_ascii=False)
    _db.execute(
        "UPDATE roadmap_items SET title=?, description=?, status=?, priority=?, category=?, subtasks=?, updated_at=? WHERE id=?",
        [
            body.get("title") or "",
            body.get("description") or "",
            body.get("status") or "todo",
            body.get("priority") or "medium",
            body.get("category") or "feature",
            subtasks,
            now,
            item_id,
        ],
    )
    return {"ok": True, "updated_at": now}


@router.delete("/{item_id}")
def delete_item(item_id: str):
    """删除任务。"""
    _ensure_table()
    existing = _db.query_list("SELECT id FROM roadmap_items WHERE id = ?", [item_id])
    if not existing:
        raise HTTPException(status_code=404, detail="任务不存在")
    _db.execute("DELETE FROM roadmap_items WHERE id = ?", [item_id])
    return {"ok": True}


@router.post("/clear-done")
def clear_done():
    """清理所有已完成的任务。"""
    _ensure_table()
    rows = _db.query_list("SELECT COUNT(*) FROM roadmap_items WHERE status = 'done'")
    count = rows[0][0] if rows and rows[0] else 0
    if count > 0:
        _db.execute("DELETE FROM roadmap_items WHERE status = 'done'")
    return {"removed": count}
