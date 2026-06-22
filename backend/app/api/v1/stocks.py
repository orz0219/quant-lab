"""股票列表与 K 线接口。"""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException

from app.core.config import settings
from app.core.database import DuckDBPool
from app.services.stock_service import StockService
from app.schemas.stock import StockListResponse, KlineData

router = APIRouter()
_db = DuckDBPool(settings.DB_PATH)
_service = StockService(_db)


@router.get("", response_model=StockListResponse)
def list_stocks(
    search: Optional[str] = Query(None, description="按股票代码或名称模糊匹配"),
    limit: int = Query(10000, ge=1, le=10000),
):
    _db.ensure_tables_exist()
    return _service.list_stocks(search=search, limit=limit)


@router.get("/by_industry")
def list_stocks_by_industry(
    industry: str = Query(..., description="行业名称"),
    limit: int = Query(500, ge=1, le=1000),
):
    """按行业返回股票列表，含最新价格和涨跌幅，按涨幅降序排列。"""
    _db.ensure_tables_exist()
    rows = _db.query_list(
        """SELECT s.ts_code, s.name,
                  d.close, d.pct_chg
           FROM stock_info s
           JOIN daily d ON s.ts_code = d.ts_code
           WHERE s.industry = ?
             AND d.trade_date = (SELECT MAX(trade_date) FROM daily)
           ORDER BY d.pct_chg DESC NULLS LAST
           LIMIT ?""",
        [industry, limit],
    )
    return [
        {"ts_code": r[0], "name": r[1], "close": round(float(r[2]), 2) if r[2] else None,
         "pct_chg": round(float(r[3]), 2) if r[3] is not None else None}
        for r in rows
    ]


@router.get("/{ts_code}/kline", response_model=List[KlineData])
def get_kline(
    ts_code: str,
    start_date: Optional[int] = Query(None, ge=20000101, le=21001231),
    end_date: Optional[int] = Query(None, ge=20000101, le=21001231),
    table: str = Query("daily", regex="^(daily|weekly)$"),
):
    _db.ensure_tables_exist()
    items = _service.get_klines(ts_code, start_date=start_date, end_date=end_date, table=table)
    if not items:
        raise HTTPException(status_code=404, detail="该股票无 K 线数据")
    return items
