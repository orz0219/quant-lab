"""全局配置。读取优先级：.env 文件 > 环境变量 > 默认值。"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


class Settings:
    DB_PATH: str = os.getenv(
        "DB_PATH",
        str(PROJECT_ROOT / "data" / "db" / "stock.duckdb"),
    )
    TUSHARE_TOKEN: str = os.getenv("TUSHARE_TOKEN", "")
    DEFAULT_START_DATE: int = 20250101

    # 输入/输出路径
    CSV_1_PATH: str = str(PROJECT_ROOT / "data" / "raw" / "1.csv")


settings = Settings()
