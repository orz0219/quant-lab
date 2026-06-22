"""验证脚本：确认核心功能仍然正常。

运行方式（任选其一）:
    cd backend && python tests/verify_cleanup.py
    python backend/tests/verify_cleanup.py
"""
import sys
from datetime import date
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

passed = []
failed = []


def record(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    message = f"[{status}] {name}"
    if detail:
        message += f"  ({detail})"
    print(message)
    (passed if ok else failed).append(name)


print("\n=== Step 1: 导入核心模块 ===")
modules_to_import = [
    "app.core.config",
    "app.core.models",
    "app.core.database",
    "app.data.sources.tushare_client",
    "app.data.pipeline.csv_importer",
    "app.data.pipeline.weekly_builder",
    "app.exporter.excel_exporter",
    "app.exporter.image_exporter",
    "app.services.stock_service",
    "app.services.backtest_service",
    "app.services.strategy_service",
    "app.schemas.stock",
    "app.schemas.backtest",
    "app.api.v1.stocks",
    "app.api.v1.backtest",
    "app.api.v1.strategy",
]

for mod in modules_to_import:
    try:
        __import__(mod)
        record(f"import {mod}", True)
    except Exception as exc:
        record(f"import {mod}", False, f"{type(exc).__name__}: {exc}")

try:
    from app.main import app  # noqa: F401
    record("import app.main", True, f"routes = {len(app.routes)}")
except Exception as exc:
    record("import app.main", False, f"{type(exc).__name__}: {exc}")


print("\n=== Step 2: DuckDBPool 连接与查询 ===")

from app.core.config import settings
from app.core.database import DuckDBPool

db = DuckDBPool(settings.DB_PATH)
record("DuckDBPool 实例化", True, f"db_path={settings.DB_PATH}")

tables = ["daily", "weekly", "stock_info"]
try:
    db.ensure_tables_exist()
    record("ensure_tables_exist", True)
except Exception as exc:
    record("ensure_tables_exist", False, f"{type(exc).__name__}: {exc}")

for table in tables:
    try:
        rows = db.query_list(f"SELECT COUNT(*) FROM {table}")
        count = rows[0][0] if rows else 0
        record(f"SELECT COUNT(*) FROM {table}", True, f"rows={count}")
    except Exception as exc:
        record(f"SELECT COUNT(*) FROM {table}", False, f"{type(exc).__name__}: {exc}")


print("\n=== Step 3: AI 策略生成 (无网络) ===")

from app.services.strategy_service import StrategyService
from app.schemas.backtest import StrategyGenerateRequest

service = StrategyService()
resp = service.generate(StrategyGenerateRequest(description="MA5 上穿 MA20 买入，下穿卖出"))
ok = bool(resp.generated_code) and "Strategy" in resp.generated_code
record("StrategyService.generate(MA)", ok,
       f"code_length={len(resp.generated_code)}, warning={resp.warning}")


print("\n=== Step 4: CLI 脚本存在性 ===")

scripts_dir = PROJECT_ROOT / "scripts"
required_scripts = [
    "run_daily_pipeline.py",
    "fetch_daily_data.py",
]

for name in required_scripts:
    path = scripts_dir / name
    ok = path.is_file()
    record(name, ok, f"path={path}")


print("\n==================================")
print(f"  总计: {len(passed) + len(failed)}")
print(f"  通过: {len(passed)}")
print(f"  失败: {len(failed)}")
print("==================================")

if failed:
    sys.exit(1)
