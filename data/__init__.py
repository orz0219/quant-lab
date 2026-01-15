from datetime import datetime, timedelta

import pandas as pd
import tushare as ts


def select_new_data(trade_date):
    ts.set_token('dc2bbdf3938e0a303770329971c6f0679d1b74c99ea74c9623ebd5c3')
    pro = ts.pro_api()
    df = pro.daily(trade_date=trade_date)
    return df

def select_data():

    start_str = "20250920"  # 修改为合理起始日
    end_date = datetime.today()  # 2026-01-15

    start_date = datetime.strptime(start_str, "%Y%m%d")
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
    # to_new_parquet()
    # selectNewData()
    df = pd.read_parquet('20260115.parquet')
    # for h in df.head():
    #     print(h)
    # print(df['trade_date'].max())
    # df = df[df['ts_code'] == '000001.SZ']
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    df = df.sort_values(by=['ts_code', 'trade_date'], ascending=[True, True])
    df['EMA5'] = round(df['close'].ewm(span=5, adjust=False).mean(),2)
    df['EMA21'] = round(df['close'].ewm(span=21, adjust=False).mean(),2)
    df['EMA55'] = round(df['close'].ewm(span=55, adjust=False).mean(),2)
    df['EMA144'] = round(df['close'].ewm(span=144, adjust=False).mean(),2)

    df = df.query('EMA5 > EMA144').query('EMA21 > EMA55').query('trade_date == 20260115')
    df.to_csv('20260115.csv', index=False)

