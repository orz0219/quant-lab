"""将 week_check 信号导出为 Excel。"""
from typing import Optional
from pathlib import Path
import pandas as pd

from app.core.database import DuckDBPool


class ExcelExporter:
    def __init__(self, db: DuckDBPool):
        self.db = db

    def export(self, output_path: str) -> int:
        sql = "SELECT * FROM week_check ORDER BY ts_code, trade_date"
        try:
            df = self.db.query_df(sql)
        except Exception:
            return 0
        if df.empty:
            return 0
        df.to_excel(output_path, index=False)
        return len(df)
