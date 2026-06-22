"""从 CSV 文件导入日线到 DuckDB daily 表。"""
import pandas as pd

from app.core.database import DuckDBPool


class CsvImporter:
    def __init__(self, db: DuckDBPool):
        self.db = db

    def import_daily_csv(self, csv_path: str) -> int:
        df = pd.read_csv(csv_path)
        if df.empty:
            return 0
        self.db.insert_df("daily", df)
        return len(df)
