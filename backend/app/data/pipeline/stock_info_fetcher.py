"""从 Tushare 拉取股票基础信息。"""
from app.core.database import DuckDBPool
from app.data.sources.tushare_client import TushareClient


class StockInfoFetcher:
    def __init__(self, db: DuckDBPool, tushare: TushareClient):
        self.db = db
        self.tushare = tushare

    def refresh(self) -> int:
        self.db.execute("DELETE FROM stock_info")
        df = self.tushare.fetch_stock_basic()
        if df.empty:
            return 0
        self.db.insert_df("stock_info", df)
        return len(df)
