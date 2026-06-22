"""从 Tushare pro.daily(trade_date='YYYYMMDD') 按日拉取日线到 daily 表。

用法：
    cd backend && python scripts/fetch_daily_data.py

行为：从库里最大日期 +1 拉到今天；已存在的日期自动跳过。
"""
import sys
from pathlib import Path


def _find_backend_root(start: Path) -> Path:
    cursor = start.resolve()
    for _ in range(8):
        if (cursor / "app" / "main.py").is_file():
            return cursor
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    return start.resolve().parent.parent


PROJECT_ROOT = _find_backend_root(Path(__file__))
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database import DuckDBPool  # noqa: E402
from app.data.sources.tushare_client import TushareClient  # noqa: E402
from app.data.pipeline.daily_fetcher import DailyFetcher  # noqa: E402


def main() -> int:
    if not settings.TUSHARE_TOKEN:
        print("[错误] 未检测到 TUSHARE_TOKEN。")
        return 1

    db = DuckDBPool(settings.DB_PATH)
    db.ensure_tables_exist()
    total = DailyFetcher(db, TushareClient(settings.TUSHARE_TOKEN)).fetch()

    row = db.query_list(
        "SELECT MIN(trade_date), MAX(trade_date), COUNT(DISTINCT ts_code) FROM daily"
    )
    if row and row[0]:
        print(f"[daily] {row[0][2]} 只股票 / {row[0][0]} -> {row[0][1]}")
    print(f"[完成] 本次共新增 {total} 行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
