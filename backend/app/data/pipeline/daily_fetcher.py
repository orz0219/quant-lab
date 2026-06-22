"""通过 Tushare pro.daily(trade_date='YYYYMMDD') 按日拉取日线并写入 daily 表。

唯一入口：fetch() —— 从"库里最大日期 +1"拉到今天，跳过已存在的日期。
"""
import time
from datetime import date, timedelta

from app.core.database import DuckDBPool
from app.data.sources.tushare_client import TushareClient


class DailyFetcher:
    def __init__(self, db: DuckDBPool, tushare: TushareClient):
        self.db = db
        self.tushare = tushare

    def fetch(self) -> int:
        """从库里最大日期拉到今天。若库里为空则从今天-7天起。"""
        last = self.db.query_scalar("SELECT MAX(trade_date) FROM daily")
        if last:
            s = str(int(last))
            start = date(int(s[:4]), int(s[4:6]), int(s[6:8])) + timedelta(days=1)
        else:
            start = date.today() - timedelta(days=7)
        end = date.today()

        total = 0
        cur = start
        while cur <= end:
            td = cur.strftime("%Y%m%d")
            if self._exists(int(td)):
                print(f"[DailyFetcher] {td} 已存在，跳过")
            else:
                df = self.tushare.fetch_daily_by_date(td)
                if df is None or getattr(df, "empty", True):
                    print(f"[DailyFetcher] {td} 无数据")
                else:
                    df = df.drop_duplicates(subset=["ts_code", "trade_date"])
                    self.db.insert_df("daily", df)
                    total += len(df)
                    print(f"[DailyFetcher] {td} 新增 {len(df)} 行")
                time.sleep(2)
            cur += timedelta(days=1)
        return total

    def _exists(self, trade_date_int: int) -> bool:
        cnt = self.db.query_scalar(
            "SELECT COUNT(*) FROM daily WHERE trade_date = ?", [trade_date_int]
        )
        return bool(cnt)
