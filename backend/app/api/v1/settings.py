"""用户指标设置接口。"""
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Body, HTTPException

from app.core.config import settings as app_settings
from app.core.database import DuckDBPool

router = APIRouter()
_db = DuckDBPool(app_settings.DB_PATH)


@router.get("/indicators")
def get_indicator_settings(user_id: str = "default"):
    """获取用户指标设置。"""
    _db.ensure_tables_exist()
    rows = _db.query_list(
        "SELECT settings FROM indicator_settings WHERE user_id = ?",
        [user_id],
    )
    if not rows:
        return {"user_id": user_id, "settings": {}}
    try:
        return {"user_id": user_id, "settings": json.loads(rows[0][0])}
    except (json.JSONDecodeError, TypeError):
        return {"user_id": user_id, "settings": {}}


@router.put("/indicators")
def save_indicator_settings(
    user_id: str = Body("default"),
    settings: dict = Body(...),
):
    """保存用户指标设置。"""
    _db.ensure_tables_exist()
    now = datetime.utcnow().isoformat()
    settings_json = json.dumps(settings, ensure_ascii=False)
    _db.execute(
        "INSERT OR REPLACE INTO indicator_settings (user_id, settings, updated_at) VALUES (?, ?, ?)",
        [user_id, settings_json, now],
    )
    return {"ok": True, "user_id": user_id}
