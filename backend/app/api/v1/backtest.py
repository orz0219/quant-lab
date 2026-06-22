"""回测接口。"""
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.database import DuckDBPool
from app.services.backtest_service import BacktestService
from app.schemas.backtest import BacktestRequest, BacktestResult

router = APIRouter()
_db = DuckDBPool(settings.DB_PATH)
_service = BacktestService(_db)


@router.post("", response_model=BacktestResult)
def run_backtest(request: BacktestRequest):
    _db.ensure_tables_exist()
    try:
        return _service.run(request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"回测执行失败：{exc}") from exc
