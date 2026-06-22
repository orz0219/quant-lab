"""DuckDB 连接工厂与 CRUD 封装。"""
import duckdb
import pandas as pd
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Any


class DuckDBPool:
    def __init__(self, db_path: str):
        # 确保父目录存在，避免首次使用时建表失败
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

    @contextmanager
    def session(self) -> Iterator[duckdb.DuckDBPyConnection]:
        conn = duckdb.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def query_df(self, sql: str, params: Optional[list[Any]] = None) -> pd.DataFrame:
        with self.session() as conn:
            if params:
                return conn.execute(sql, params).df()
            return conn.sql(sql).df()

    def query_list(self, sql: str, params: Optional[list[Any]] = None) -> list[tuple]:
        with self.session() as conn:
            if params:
                return conn.execute(sql, params).fetchall()
            return conn.execute(sql).fetchall()

    def query_scalar(self, sql: str, params: Optional[list[Any]] = None) -> Any:
        rows = self.query_list(sql, params)
        return rows[0][0] if rows and rows[0] else None

    def execute(self, sql: str, params: Optional[list[Any]] = None) -> None:
        with self.session() as conn:
            if params:
                conn.execute(sql, params)
            else:
                conn.execute(sql)

    def executemany(self, sql: str, rows: list[tuple]) -> None:
        with self.session() as conn:
            conn.executemany(sql, rows)

    def insert_df(self, table: str, df: pd.DataFrame) -> None:
        with self.session() as conn:
            conn.register("_temp_df", df)
            conn.execute(f"INSERT INTO {table} SELECT * FROM _temp_df")

    def insert_many(self, table: str, rows: list[tuple], columns: list[str]) -> None:
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"
        self.executemany(sql, rows)

    def ensure_tables_exist(self) -> None:
        with self.session() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_versions (
                    id VARCHAR,
                    version INTEGER,
                    name VARCHAR,
                    description VARCHAR DEFAULT '',
                    tags VARCHAR DEFAULT '',
                    code TEXT NOT NULL,
                    params_schema TEXT DEFAULT '{}',
                    dependencies TEXT DEFAULT '[]',
                    checksum VARCHAR DEFAULT '',
                    saved_at VARCHAR DEFAULT '',
                    PRIMARY KEY (id, version)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_strategies (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description VARCHAR DEFAULT '',
                tags VARCHAR DEFAULT '',
                code TEXT NOT NULL,
                params_schema TEXT DEFAULT '{}',
                dependencies TEXT DEFAULT '[]',
                version INTEGER DEFAULT 1,
                checksum VARCHAR DEFAULT '',
                is_builtin BOOLEAN DEFAULT FALSE,
                created_at VARCHAR DEFAULT '',
                updated_at VARCHAR DEFAULT ''
            )
        """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily (
                    ts_code VARCHAR, trade_date INTEGER,
                    open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
                    pre_close DOUBLE, change DOUBLE, pct_chg DOUBLE,
                    vol DOUBLE, amount DOUBLE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weekly (
                    ts_code VARCHAR, trade_date INTEGER,
                    open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
                    vol DOUBLE, amount DOUBLE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS week_check (
                    ts_code VARCHAR, trade_date INTEGER,
                    price_open DOUBLE, price_high DOUBLE, price_low DOUBLE, price_close DOUBLE,
                    pin_bar_tag VARCHAR, radio DOUBLE, win_p DOUBLE, lose_p DOUBLE,
                    near_high DOUBLE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_info (
                    ts_code VARCHAR, symbol VARCHAR, name VARCHAR,
                    area VARCHAR, industry VARCHAR, market VARCHAR
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sector_rs (
                    trade_date INTEGER NOT NULL,
                    industry VARCHAR NOT NULL,
                    sector_return DOUBLE NOT NULL,
                    market_return DOUBLE NOT NULL,
                    rs DOUBLE NOT NULL,
                    stock_count INTEGER NOT NULL DEFAULT 0,
                    calculated_at VARCHAR DEFAULT '',
                    PRIMARY KEY (trade_date, industry)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sector_rs_cache (
                    trade_date INTEGER NOT NULL,
                    industry VARCHAR NOT NULL,
                    rs DOUBLE NOT NULL,
                    sector_return DOUBLE NOT NULL DEFAULT 0,
                    market_return DOUBLE NOT NULL DEFAULT 0,
                    stock_count INTEGER NOT NULL DEFAULT 0,
                    calculated_at VARCHAR DEFAULT '',
                    PRIMARY KEY (trade_date, industry)
                )
            """)
            # 迁移：旧表有 rs_ma5 列则删除
            conn.execute("ALTER TABLE sector_rs_cache DROP COLUMN IF EXISTS rs_ma5")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS indicator_settings (
                    user_id VARCHAR DEFAULT 'default',
                    settings TEXT DEFAULT '{}',
                    updated_at VARCHAR DEFAULT '',
                    PRIMARY KEY (user_id)
                )
            """)
