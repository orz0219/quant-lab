"""一键跑完整流程：数据采集 -> 周线合成。

用法（任选其一）:
    cd backend && python scripts/run_daily_pipeline.py [--start-date 20250101] [--use-tushare | --use-csv]
    python backend/scripts/run_daily_pipeline.py
"""
import sys
import argparse
from pathlib import Path


def _find_backend_root(start: Path) -> Path:
    cursor = start.resolve()
    for _ in range(8):
        if (cursor / "app" / "main.py").is_file():
            return cursor
        if cursor.parent == cursor:
            break
    return start.resolve().parent.parent


PROJECT_ROOT = _find_backend_root(Path(__file__))
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database import DuckDBPool
from app.data.sources.tushare_client import TushareClient
from app.data.pipeline import DailyFetcher, StockInfoFetcher, CsvImporter, WeeklyBuilder


def main():
    parser = argparse.ArgumentParser(description="股票数据处理流水线")
    parser.add_argument("--start-date", type=int, default=settings.DEFAULT_START_DATE)
    parser.add_argument("--use-tushare", action="store_true")
    parser.add_argument("--use-csv", action="store_true")
    args = parser.parse_args()

    db = DuckDBPool(settings.DB_PATH)
    db.ensure_tables_exist()

    if args.use_tushare and settings.TUSHARE_TOKEN:
        tushare = TushareClient(settings.TUSHARE_TOKEN)
        daily = DailyFetcher(db, tushare)
        n = daily.fetch()
        print(f"[Tushare] 新增日线 {n} 行")
        info = StockInfoFetcher(db, tushare)
        n = info.refresh()
        print(f"[Tushare] 股票基础信息 {n} 行")
    elif args.use_csv:
        importer = CsvImporter(db)
        n = importer.import_daily_csv(settings.CSV_1_PATH)
        print(f"[CSV] 导入日线 {n} 行")
    else:
        print("[数据] 跳过采集（若要采集，请加 --use-tushare 或 --use-csv）")

    builder = WeeklyBuilder(db)
    n = builder.build_all(args.start_date)
    print(f"[周线] 写入 weekly 表 {n} 行")

    print("\n=== 流水线完成 ===")


if __name__ == "__main__":
    main()
