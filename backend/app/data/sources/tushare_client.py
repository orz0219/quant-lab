"""Tushare API 封装：日线 + 股票基础信息。"""
import pandas as pd
from typing import Optional

try:
    import tushare as ts
    _TUSHARE_AVAILABLE = True
except ImportError:
    ts = None
    _TUSHARE_AVAILABLE = False


class TushareClient:
    def __init__(self, token: str):
        if not _TUSHARE_AVAILABLE:
            raise ImportError("tushare 未安装。请先 pip install tushare。")
        if not token:
            raise ValueError("TUSHARE_TOKEN 为空，请在 .env 文件或环境变量中配置。")
        ts.set_token(token)
        self.pro = ts.pro_api()

    def fetch_daily(self, start_date: str, end_date: str, ts_code: Optional[str] = None) -> pd.DataFrame:
        if ts_code:
            return self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return self.pro.daily(start_date=start_date, end_date=end_date)

    def fetch_daily_by_date(self, trade_date: str) -> pd.DataFrame:
        """按交易日取当天所有股票的日线：pro.daily(trade_date='YYYYMMDD')。"""
        return self.pro.daily(trade_date=trade_date)

    def fetch_stock_basic(self) -> pd.DataFrame:
        return self.pro.stock_basic(
            exchange="", list_status="L",
            fields="ts_code,symbol,name,area,industry,market",
        )
