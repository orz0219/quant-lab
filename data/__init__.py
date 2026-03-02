from datetime import datetime, timedelta

import pandas as pd
import tushare as ts
import duckdb

# 链接数据库
con = duckdb.connect('stock.duckdb')

def select_new_data(trade_date):
    ts.set_token('dc2bbdf3938e0a303770329971c6f0679d1b74c99ea74c9623ebd5c3')
    pro = ts.pro_api()
    df = pro.daily(trade_date=trade_date)
    return df

def select_data():
    last_date = con.sql("""
        select max(trade_date) from daily
    """).fetchone()
    start_str = str(last_date[0])  # 修改为合理起始日
    end_date = datetime.today()  # 2026-01-15

    start_date = datetime.strptime(start_str, "%Y%m%d")
    start_date = start_date + timedelta(days=1)
    current = start_date
    x = pd.DataFrame([])
    while current <= end_date:
        d = current.strftime("%Y%m%d")
        print(d)
        df = select_new_data(d)
        current += timedelta(days=1)
        if df.shape[0] == 0:
            continue
        x =  pd.concat([x, df])
    pd.concat([x]).to_csv('1.csv', index=False)


def to_new_parquet():
    today = datetime.today()
    d1 = pd.read_parquet('all.parquet')
    d2 = pd.read_csv('all2.csv')
    d3 = pd.concat([d1, d2])
    d3.to_parquet(today.strftime("%Y%m%d") + '.parquet')





if __name__ == '__main__':
    select_data()
    # df['EMA5'] = round(df['close'].ewm(span=5, adjust=False).mean(),2)
    # df['EMA21'] = round(df['close'].ewm(span=21, adjust=False).mean(),2)
    # df['EMA55'] = round(df['close'].ewm(span=55, adjust=False).mean(),2)
    # df['EMA144'] = round(df['close'].ewm(span=144, adjust=False).mean(),2)
    # df['B1'] = (df['EMA144'].shift(1) < df['EMA144']) & (df['EMA144'] < df['EMA5']) & (df['EMA5'].shift(10) < df['EMA144'].shift(10)) & (df['EMA21'] > df['EMA55'])
    # df['B2'] = (df['EMA144'].shift(1) < df['EMA144']) & (df['EMA144'] < df['EMA5']) & (df['EMA21'].shift(10) < df['EMA144'].shift(10)) & (df['EMA21'] > df['EMA55']) & (df['EMA21'] > df['EMA144'])
    # df = df.query('B2')
    # df.to_csv('20260115B3.csv', index=False)

