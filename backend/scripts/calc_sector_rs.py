#!/usr/bin/env python3
"""增量计算行业板块 RS，写入 sector_rs_cache 表。

用法:
    cd backend
    python3 scripts/calc_sector_rs.py

说明:
    - RS = 板块过去 N 日累积涨幅 / |全市场过去 N 日累积涨幅|（价格动量 RS）
          N 默认 20 个交易日，可在脚本中调整 MOMENTUM_DAYS
    - 增量模式：只计算缺失日期，已有数据不重算
    - 每次约 1~3 秒完成（新增 1 天数据时）
"""
import sys
import time
from datetime import datetime, timedelta
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

from app.core.config import settings
from app.core.database import DuckDBPool


def calc_and_store():
    db = DuckDBPool(settings.DB_PATH)
    db.ensure_tables_exist()

    t0 = time.time()
    now = datetime.utcnow().isoformat()
    MOMENTUM_DAYS = 20

    # 1. 找到上次计算的最后日期
    last_date = db.query_scalar(
        "SELECT MAX(trade_date) FROM sector_rs_cache"
    )

    # 2. 找到 daily 中需要新增的交易日
    if last_date is None:
        # 首次运行：全量计算
        new_dates = db.query_list(
            "SELECT DISTINCT d.trade_date FROM daily d "
            "WHERE d.pct_chg IS NOT NULL ORDER BY d.trade_date"
        )
        date_from = 0
    else:
        new_dates = db.query_list(
            "SELECT DISTINCT d.trade_date FROM daily d "
            "WHERE d.trade_date > ? AND d.pct_chg IS NOT NULL "
            "ORDER BY d.trade_date",
            [last_date],
        )
        # 按交易日往前取 25 天，确保 20 日窗口完整（非日历天）
        date_row = db.query_list(
            "SELECT trade_date FROM daily WHERE trade_date <= ? AND pct_chg IS NOT NULL ORDER BY trade_date DESC LIMIT 1 OFFSET ?",
            [last_date, MOMENTUM_DAYS + 5],
        )
        date_from = date_row[0][0] if date_row else 0

    new_days = [r[0] for r in new_dates]

    if not new_days:
        print("  无新增数据，跳过。")
        return

    date_to = max(new_days)
    print(f"  已有数据截止: {last_date or '无'}, 新增交易日: {len(new_days)} 个 ({new_days[0]} ~ {date_to})")

    # 3. 计算 RS
    print("  SQL 查询中...", end='', flush=True)
    t1 = time.time()
    sql = f"""
        WITH daily_base AS MATERIALIZED (
            SELECT d.trade_date, d.ts_code, d.pct_chg, COALESCE(s.industry, '其他') AS industry
            FROM daily d
            LEFT JOIN stock_info s ON d.ts_code = s.ts_code
            WHERE d.pct_chg IS NOT NULL
              AND d.trade_date >= {date_from}
              AND d.trade_date <= {date_to}
        ),
        industry_avg AS (
            SELECT trade_date, industry, AVG(pct_chg) AS sector_return,
                   COUNT(DISTINCT ts_code) AS stock_count
            FROM daily_base
            GROUP BY trade_date, industry
        ),
        market_avg AS MATERIALIZED (
            SELECT trade_date, AVG(pct_chg) AS market_return
            FROM daily_base
            GROUP BY trade_date
        ),
        market_momentum AS (
            SELECT trade_date, market_return,
                   SUM(market_return) OVER (
                       ORDER BY trade_date
                       ROWS BETWEEN {MOMENTUM_DAYS - 1} PRECEDING AND CURRENT ROW
                   ) AS market_accum
            FROM market_avg
        ),
        momentum AS (
            SELECT i.trade_date, i.industry, i.sector_return, m.market_return,
                   i.stock_count, m.market_accum,
                   SUM(i.sector_return) OVER (
                       PARTITION BY i.industry
                       ORDER BY i.trade_date
                       ROWS BETWEEN {MOMENTUM_DAYS - 1} PRECEDING AND CURRENT ROW
                   ) AS sector_accum
            FROM industry_avg i
            JOIN market_momentum m ON i.trade_date = m.trade_date
        )
        SELECT trade_date, industry,
               CASE
                   WHEN ABS(market_accum) > 1e-8 THEN sector_accum / ABS(market_accum)
                   WHEN sector_accum > 1e-8 THEN 3.0
                   WHEN sector_accum < -1e-8 THEN -3.0
                   ELSE 0.0
               END AS rs,
               sector_return, market_return, stock_count
        FROM momentum
        WHERE trade_date IN ({','.join(str(d) for d in new_days)})
        ORDER BY trade_date, industry
    """

    rows = db.query_list(sql)
    t2 = time.time()
    print(f"  SQL 查询完成 ({t2 - t1:.1f}s)，共 {len(rows)} 行")

    if not rows:
        print("  无数据，退出。")
        return

    # 4. 写入数据（分批 + 进度条）
    insert_sql = """INSERT OR REPLACE INTO sector_rs_cache
        (trade_date, industry, rs, sector_return, market_return, stock_count, calculated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)"""

    BATCH_SIZE = 1000
    total = len(rows)
    written = 0
    for i in range(0, total, BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]
        batch = [
            (int(td), str(ind), float(rs_val), float(sec_ret), float(mkt_ret), int(cnt), now)
            for td, ind, rs_val, sec_ret, mkt_ret, cnt in chunk
        ]
        db.executemany(insert_sql, batch)
        written += len(chunk)
        pct = int(written / total * 100)
        bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
        print(f"\r  写入中 [{bar}] {pct}% ({written}/{total})", end='', flush=True)

    print()
    elapsed = time.time() - t0
    print(f"  完成，总耗时 {elapsed:.1f} 秒")


if __name__ == "__main__":
    print("增量计算行业板块 RS...")
    calc_and_store()
