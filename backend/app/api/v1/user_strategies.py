"""用户自定义策略 CRUD 接口。"""
import json
import hashlib
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from app.core.config import settings
from app.core.database import DuckDBPool

router = APIRouter()
_db = DuckDBPool(settings.DB_PATH)


def _checksum(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


def _row_to_dict(row: tuple, cols: list[str]) -> dict:
    d = {}
    for i, c in enumerate(cols):
        val = row[i]
        if c in ("params_schema", "dependencies"):
            try:
                val = json.loads(val) if isinstance(val, str) else val
            except (json.JSONDecodeError, TypeError):
                val = {} if c == "params_schema" else []
        d[c] = val
    return d


COLS = [
    "id", "name", "description", "tags", "code",
    "params_schema", "dependencies", "version", "checksum",
    "is_builtin", "created_at", "updated_at",
]


@router.get("")
def list_strategies(
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """返回策略元数据列表（不含 code）。"""
    _db.ensure_tables_exist()
    keyword = (search or "").strip()
    sql = "SELECT id, name, description, tags, version, checksum, is_builtin, created_at, updated_at FROM user_strategies WHERE 1=1"
    params: list = []
    if keyword:
        sql += " AND (UPPER(name) LIKE UPPER(?) OR UPPER(description) LIKE UPPER(?))"
        like = f"%{keyword}%"
        params.extend([like, like])
    sql += " ORDER BY is_builtin DESC, created_at DESC LIMIT ?"
    params.append(limit)
    rows = _db.query_list(sql, params)
    keys = ["id", "name", "description", "tags", "version", "checksum", "is_builtin", "created_at", "updated_at"]
    items = [_row_to_dict(r, keys) for r in rows]
    return {"total": len(items), "items": items}


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str):
    """返回完整策略（含 code），支持 checksum 缓存。"""
    _db.ensure_tables_exist()
    rows = _db.query_list(
        f"SELECT {', '.join(COLS)} FROM user_strategies WHERE id = ?",
        [strategy_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="策略不存在")
    return _row_to_dict(rows[0], COLS)


@router.post("", status_code=201)
def create_strategy(body: dict):
    """创建新策略。"""
    _db.ensure_tables_exist()
    sid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="策略名称不能为空")
    code = body.get("code") or ""
    if not code:
        raise HTTPException(status_code=400, detail="策略代码不能为空")
    csum = _checksum(code)
    params_schema = json.dumps(body.get("params_schema", {}), ensure_ascii=False)
    deps = json.dumps(body.get("dependencies", []), ensure_ascii=False)
    tags = body.get("tags") or ""
    desc = body.get("description") or ""
    _db.execute(
        "INSERT INTO user_strategies (id, name, description, tags, code, params_schema, dependencies, version, checksum, is_builtin, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, FALSE, ?, ?)",
        [sid, name, desc, tags, code, params_schema, deps, csum, now, now],
    )
    return {"id": sid, "checksum": csum, "version": 1}


@router.put("/{strategy_id}")
def update_strategy(strategy_id: str, body: dict):
    """更新策略（版本号+1），旧版本自动存入 strategy_versions。"""
    _db.ensure_tables_exist()
    existing = _db.query_list(
        "SELECT id, name, description, tags, code, params_schema, dependencies, version, checksum FROM user_strategies WHERE id = ?",
        [strategy_id],
    )
    if not existing:
        raise HTTPException(status_code=404, detail="策略不存在")
    now = datetime.utcnow().isoformat()
    old = existing[0]
    old_ver = old[7]

    # 保存当前版本到历史表
    _db.execute(
        "INSERT OR REPLACE INTO strategy_versions (id, version, name, description, tags, code, params_schema, dependencies, checksum, saved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [strategy_id, old_ver, old[1], old[2], old[3], old[4], old[5], old[6], old[8], now],
    )

    code = body.get("code") or ""
    csum = _checksum(code) if code else ""
    params_schema = json.dumps(body.get("params_schema", {}), ensure_ascii=False)
    deps = json.dumps(body.get("dependencies", []), ensure_ascii=False)
    _db.execute(
        "UPDATE user_strategies SET name=?, description=?, tags=?, code=?, params_schema=?, dependencies=?, version=?, checksum=?, updated_at=? WHERE id=?",
        [
            body.get("name", ""),
            body.get("description", ""),
            body.get("tags", ""),
            code,
            params_schema,
            deps,
            old_ver + 1,
            csum,
            now,
            strategy_id,
        ],
    )
    return {"id": strategy_id, "checksum": csum, "version": old_ver + 1}


@router.get("/{strategy_id}/versions")
def list_versions(strategy_id: str):
    """返回策略的所有历史版本。"""
    _db.ensure_tables_exist()
    rows = _db.query_list(
        "SELECT version, name, description, tags, code, params_schema, checksum, saved_at FROM strategy_versions WHERE id = ? ORDER BY version DESC",
        [strategy_id],
    )
    keys = ["version", "name", "description", "tags", "code", "params_schema", "checksum", "saved_at"]
    items = [_row_to_dict(r, keys) for r in rows]
    return {"items": items}


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: str):
    """删除策略。"""
    _db.ensure_tables_exist()
    existing = _db.query_list("SELECT id FROM user_strategies WHERE id = ?", [strategy_id])
    if not existing:
        raise HTTPException(status_code=404, detail="策略不存在")
    _db.execute("DELETE FROM user_strategies WHERE id = ?", [strategy_id])
    return {"ok": True}
