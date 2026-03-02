from datetime import datetime, timedelta

import duckdb
import pandas as pd

# 链接数据库
con = duckdb.connect('stock.duckdb')

def add_db():
    df = pd.read_csv('1.csv')
    # 插入数据（df 是你的 pandas DataFrame）
    con.register('df_input', df)
    con.execute("INSERT INTO daily SELECT * FROM df_input")

def get_monday(date_str=None, fmt='%Y%m%d'):
    if date_str is None:
        date_str = datetime.today().strftime('%Y%m%d')
    dt = datetime.strptime(date_str, fmt)
    monday = dt - timedelta(days=dt.weekday())  # weekday(): Monday=0, Sunday=6
    return monday.strftime(fmt)

def get_week_data(ts_code: str, td = None):
    if td is None:
        td = get_monday()

    con.sql("""
        delete from weekly WHERE ts_code = ? and trade_date >= ?
    """, params=[ts_code, td])

    data = con.sql("""
        SELECT * FROM daily WHERE ts_code = ? and trade_date >= ? ORDER BY trade_date
    """, params=[ts_code, td]).fetchall()

    if not data:
        print(f"=== {ts_code} 无日K数据 ===")
        return

    # 按周分组
    weeks = {}
    for row in data:
        ts_code_row, trade_date, o, h, l, c, *_rest, vol, amt = row
        monday = get_monday(str(trade_date))
        key = (ts_code_row, monday)

        if key not in weeks:
            weeks[key] = {
                'dates': [],
                'opens': [],
                'highs': [],
                'lows': [],
                'closes': [],
                'vols': [],
                'amounts': []
            }

        weeks[key]['dates'].append(trade_date)
        weeks[key]['opens'].append(o)
        weeks[key]['highs'].append(h)
        weeks[key]['lows'].append(l)
        weeks[key]['closes'].append(c)
        weeks[key]['vols'].append(vol)
        weeks[key]['amounts'].append(amt)

    # 生成周K（字典列表）
    weekly_k = []
    for (ts_code_key, week_start), values in weeks.items():
        weekly_k.append({
            'ts_code': ts_code_key,
            'trade_date': min(values['dates']),
            'open': values['opens'][0],
            'high': max(values['highs']),
            'low': min(values['lows']),
            'close': values['closes'][-1],
            'vol': sum(values['vols']),
            'amount': sum(values['amounts'])
        })

    if not weekly_k:
        print(f"=== {ts_code} 无法生成周K ===")
        return

    # 转为元组列表
    weekly_tuples = [
        (
            wk['ts_code'],
            wk['trade_date'],
            wk['open'],
            wk['high'],
            wk['low'],
            wk['close'],
            wk['vol'],
            wk['amount']
        )
        for wk in weekly_k
    ]

    # 去重逻辑
    new_keys = [(row[0], row[1]) for row in weekly_tuples]
    placeholders = ', '.join(['(?, ?)'] * len(new_keys))
    existing = con.execute(f"""
        SELECT ts_code, trade_date 
        FROM weekly 
        WHERE (ts_code, trade_date) IN ({placeholders})
    """, [item for pair in new_keys for item in pair]).fetchall()

    existing_set = set(existing)
    filtered_tuples = [
        row for row in weekly_tuples
        if (row[0], row[1]) not in existing_set
    ]

    # 插入新数据
    if filtered_tuples:
        con.executemany("""
            INSERT INTO weekly (ts_code, trade_date, open, high, low, close, vol, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, filtered_tuples)
        print(f"=== {ts_code} 插入 {len(filtered_tuples)} 条周K ===")
    else:
        print(f"=== {ts_code} 无新周K需要插入 ===")

    print(f"=== {ts_code} end! ===")

def code_select(yesterday_str = None):
    if yesterday_str is None:
        last_date = con.sql("""
                            select max(trade_date)
                            from daily
                            """).fetchone()
        yesterday_str = last_date[0]
    codes = con.sql("""
        select ts_code from daily where trade_date= ? and (ts_code like '00%' or ts_code like '60%') order by ts_code
    """, params=[yesterday_str]).fetchall()
    return [row[0] for row in codes]

def refresh_all():
    codes = code_select()
    for code in codes:
        get_week_data(code)

def refresh_weeks(week=None):
    codes = code_select(week)
    for code in codes:
        get_week_data(code, week)


if __name__ == '__main__':
    # 计算周K 获取每周的日期 然后查询
    # add_db()
    # refresh_weeks(20260224)
    refresh_weeks()
    # con.execute("""
    # DROP TABLE week_check""")
    #
    # con.execute(f"""
    #     CREATE TABLE IF NOT EXISTS week_check(
    #         ts_code VARCHAR,
    #         trade_date BIGINT,
    #         -- 价格和盈亏字段改为 DECIMAL(18, 4)
    #         price_open DECIMAL(18, 4),
    #         price_high DECIMAL(18, 4),
    #         price_low DECIMAL(18, 4),
    #         price_close DECIMAL(18, 4),
    #         pin_bar_tag VARCHAR
    #     )
    # """)

