import pandas as pd
import duckdb

db_path = '../data/stock.duckdb'

def hl_check(df : pd.DataFrame):

    last_h_close = 0
    last_m_close = 0
    last_highest = 0
    last_lowest = 0
    tag = 'H'
    results = []
    tag_arr = ['H', 'H']
    b2 = False
    b2_price = 0
    b2_sum = 0
    for row in df.itertuples():
        o = row.open
        c = row.close
        max_h = max(o, c)
        min_l = min(o, c)
        h = row.high
        l = row.low
        if last_h_close == 0:
            last_highest = max_h
            last_lowest = min_l
            tag = 'H'
        else:
            if max_h >= last_h_close:
                if last_highest < h or tag == 'L':
                    last_highest = h
                tag = 'H'
            elif min_l <= last_m_close:
                if last_lowest > l or tag == 'H':
                    last_lowest = l
                tag = 'L'

        last_h_close = max_h
        last_m_close = min_l

        if row.B1:
            if not b2 and  tag_arr[0] == 'L' and tag_arr[1] == 'H' and tag == 'H':
                b2 = True
                b2_price = round(row.close,2)
        if b2 and (tag_arr[1] == 'L' and tag == 'L' or b2_price < last_lowest):
            b2_sum = round(b2_sum + row.close - b2_price, 2)
            b2 = False

        tag_arr[0] = tag_arr[1]
        tag_arr[1] = tag

        results.append(
            {
                'ts_code': row.ts_code,
                'trade_date': row.trade_date,
                'open': round(row.open, 2),
                'high': round(row.high,2),
                'low': round(row.low,2),
                'close': round(row.close,2),
                'pre_close': round(row.pre_close,2),
                'change': round(row.change,2),
                'pct_chg': round(row.pct_chg,2),
                'vol': row.vol,
                'amount': round(row.amount,2),
                'EMA5': row.EMA5,
                'EMA21': row.EMA21,
                'EMA55': row.EMA55,
                'EMA144': row.EMA144,
                'HIGHEST': round(last_highest,2),  # 新增字段
                'LOWEST': round(last_lowest,2), # 新增字段
                'TAG': tag,
                'B1': row.B1,
                'B2_SUM': b2_sum
            }
        )

    return pd.DataFrame(results)







if __name__ == '__main__':
    con = duckdb.connect(db_path)
    df = con.sql("""
                    SELECT *
                    FROM daily
                    WHERE ts_code = '000007.SZ'
                    ORDER BY trade_date
                    """).df()
    df['EMA5'] = round(df['close'].ewm(span=5, adjust=False).mean(),2)
    df['EMA21'] = round(df['close'].ewm(span=21, adjust=False).mean(),2)
    df['EMA55'] = round(df['close'].ewm(span=55, adjust=False).mean(),2)
    df['EMA144'] = round(df['close'].ewm(span=144, adjust=False).mean(),2)
    df['B1'] = df['EMA144'] > df['EMA144'].shift(5)

    # 找到近期低点
    df = hl_check(df)

    con.register('df_view', df)
    con.execute("DROP TABLE IF EXISTS one_test;")
    con.execute("CREATE TABLE IF NOT EXISTS one_test AS SELECT * FROM df_view")
