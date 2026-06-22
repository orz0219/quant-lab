"""股票基础信息与 K 线数据服务。"""
from typing import List, Optional
import pandas as pd

from app.core.database import DuckDBPool
from app.core.models import Kline
from app.schemas.stock import StockInfo, KlineData, StockListResponse


class StockService:
    def __init__(self, db: DuckDBPool):
        self.db = db

    def list_stocks(self, search: Optional[str] = None, limit: int = 200) -> StockListResponse:
        """从 stock_info 拉股票列表；支持按代码或名称模糊搜索；若无 stock_info 则回退 daily 表。"""
        keyword = (search or "").strip()
        try:
            desc = self.db.query_df("DESCRIBE stock_info")
            available = set(desc["column_name"].tolist())
        except Exception:
            available = {"ts_code", "name", "area", "industry", "market"}

        has_name = "name" in available
        columns = [c for c in ["ts_code", "symbol", "name", "area", "industry", "market"] if c in available]
        items: List[StockInfo] = []
        try:
            sql = f"SELECT DISTINCT {', '.join(columns)} FROM stock_info WHERE 1=1"
            params: list = []
            if keyword:
                sql += " AND (UPPER(ts_code) LIKE UPPER(?) OR UPPER(COALESCE(name, '')) LIKE UPPER(?))"
                like = f"%{keyword}%"
                params.extend([like, like])
            sql += " ORDER BY ts_code LIMIT ?"
            params.append(limit)
            rows = self.db.query_list(sql, params)
            col_index = {name: idx for idx, name in enumerate(columns)}
            for r in rows:
                items.append(StockInfo(
                    ts_code=r[col_index["ts_code"]],
                    symbol=(r[col_index["symbol"]] if "symbol" in col_index else None),
                    name=(r[col_index["name"]] if "name" in col_index else None),
                    area=(r[col_index["area"]] if "area" in col_index else None),
                    industry=(r[col_index["industry"]] if "industry" in col_index else None),
                    market=(r[col_index["market"]] if "market" in col_index else None),
                ))
        except Exception:
            items = []

        if not items and keyword:
            # 用户搜索但 stock_info 未命中：回退 daily 表按代码搜（没有 name）
            rows = self.db.query_list(
                "SELECT DISTINCT ts_code FROM daily WHERE UPPER(ts_code) LIKE UPPER(?) ORDER BY ts_code LIMIT ?",
                [f"%{keyword}%", limit],
            )
            items = [StockInfo(ts_code=r[0]) for r in rows]
        elif not items:
            rows = self.db.query_list(
                "SELECT DISTINCT ts_code FROM daily ORDER BY ts_code LIMIT ?",
                [limit],
            )
            items = [StockInfo(ts_code=r[0]) for r in rows]
        return StockListResponse(total=len(items), items=items, has_name=has_name)

    def get_klines(self, ts_code: str, start_date: Optional[int] = None,
                   end_date: Optional[int] = None, table: str = "daily") -> List[KlineData]:
        table = table if table in ("daily", "weekly") else "daily"
        if table == "weekly":
            sql = "SELECT trade_date, open, high, low, close, vol, amount FROM weekly WHERE ts_code = ?"
        else:
            sql = "SELECT trade_date, open, high, low, close, vol, amount, pct_chg FROM daily WHERE ts_code = ?"
        params: list = [ts_code]
        if start_date:
            sql += " AND trade_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND trade_date <= ?"
            params.append(end_date)
        sql += " ORDER BY trade_date"
        rows = self.db.query_list(sql, params)
        return [
            KlineData(
                trade_date=pd.to_datetime(str(int(r[0])), format="%Y%m%d").date(),
                open=float(r[1]), high=float(r[2]), low=float(r[3]), close=float(r[4]),
                vol=float(r[5]) if r[5] is not None else 0.0,
                amount=float(r[6]) if r[6] is not None else 0.0,
                pct_chg=float(r[7]) if r[7] is not None else None,
            )
            for r in rows
        ]

    def to_model(self, row: tuple) -> Kline:
        ts_code, trade_date_int, open_v, high_v, low_v, close_v, vol_v, amount_v = row
        from datetime import datetime
        trade_date = datetime.strptime(str(int(trade_date_int)), "%Y%m%d").date()
        return Kline(
            ts_code=ts_code, trade_date=trade_date,
            open=open_v, high=high_v, low=low_v, close=close_v,
            vol=vol_v, amount=amount_v,
        )
