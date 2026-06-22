"""从 daily 表按股票聚合周线 -> 写入 weekly 表。"""
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import DuckDBPool


class WeeklyBuilder:
    def __init__(self, db: DuckDBPool):
        self.db = db

    def _get_all_codes(self, trade_date: int) -> list[str]:
        sql = """
            SELECT DISTINCT ts_code FROM daily
            WHERE trade_date = ? AND (ts_code LIKE '00%' OR ts_code LIKE '60%')
            ORDER BY ts_code
        """
        rows = self.db.query_list(sql, [trade_date])
        return [r[0] for r in rows]

    def _load_daily_for_code(self, ts_code: str, start_date: int) -> list[tuple]:
        sql = """
            SELECT ts_code, trade_date, open, high, low, close, vol, amount
            FROM daily
            WHERE ts_code = ? AND trade_date >= ?
            ORDER BY trade_date
        """
        return self.db.query_list(sql, [ts_code, start_date])

    def _build_for_code(self, ts_code: str, start_date: Optional[int] = None) -> list[tuple]:
        if start_date is None:
            row = self.db.query_list(
                "SELECT COALESCE(MIN(trade_date), 0) FROM daily WHERE ts_code = ?", [ts_code]
            )
            if not row or not row[0] or not row[0][0]:
                return []
            start_date = int(row[0][0])

        daily_rows = self._load_daily_for_code(ts_code, start_date)
        if not daily_rows:
            return []

        weeks: dict[int, dict] = {}

        for row in daily_rows:
            _, td, open_v, high_v, low_v, close_v, vol_v, amount_v = row
            td_int = int(td)
            date_obj = datetime.strptime(str(td_int), "%Y%m%d").date()

            monday = date_obj - timedelta(days=date_obj.weekday())
            monday_int = int(monday.strftime("%Y%m%d"))

            if monday_int not in weeks:
                weeks[monday_int] = {
                    "open": float(open_v),
                    "high": float(high_v),
                    "low": float(low_v),
                    "close": float(close_v),
                    "vol": float(vol_v) if vol_v is not None else 0.0,
                    "amount": float(amount_v) if amount_v is not None else 0.0,
                }
            else:
                w = weeks[monday_int]
                w["high"] = max(w["high"], float(high_v))
                w["low"] = min(w["low"], float(low_v))
                w["close"] = float(close_v)
                w["vol"] += float(vol_v) if vol_v is not None else 0.0
                w["amount"] += float(amount_v) if amount_v is not None else 0.0

        rows_to_insert = []
        for week_start, w in sorted(weeks.items()):
            rows_to_insert.append((
                ts_code, week_start,
                w["open"], w["high"], w["low"], w["close"],
                w["vol"], w["amount"],
            ))
        return rows_to_insert

    def build_all(self, start_date: Optional[int] = None) -> int:
        if start_date is None:
            row = self.db.query_list("SELECT MAX(trade_date) FROM daily")
            if not row or not row[0] or not row[0][0]:
                return 0
            latest = int(row[0][0])
        else:
            latest = start_date

        codes = self._get_all_codes(latest)

        if start_date is not None:
            self.db.execute("DELETE FROM weekly WHERE trade_date >= ?", [start_date])

        all_rows: list[tuple] = []
        for code in codes:
            all_rows.extend(self._build_for_code(code, start_date))

        if all_rows:
            columns = ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"]
            self.db.insert_many("weekly", all_rows, columns)

        return len(all_rows)
