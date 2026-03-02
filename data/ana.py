"""
有几个问题
pinBar 如何定义
压力位如何定义
支撑位如何定义
趋势线如何定义 当前趋势如何判断
盈亏比大于2怎么标记


基于pinBar的周线交易系统

pinBar的定义
小实体（开盘≈收盘）+ 单侧显著长影线（“鼻子”），影线长度通常≥实体2.5倍，且占K线总长65%以上

pinBar的合并
可以最多由3根K线组成 所以需要做一个移动数组

"""

import duckdb
import pandas as pd

# 链接数据库
con = duckdb.connect('stock.duckdb')


def check_pin_bar(open_p, high_p, low_p, close_p):
    if high_p == low_p:
        pin_bar_tag = False
    elif close_p >= open_p:
        if high_p == open_p:
            pin_bar_tag = True
        else:
            pin_bar_tag = (open_p - low_p) / (high_p - open_p) >= 2.5
    else:
        pin_bar_tag = (close_p - low_p) / (high_p - close_p) >= 2.5
    return pin_bar_tag


def check(result):
    code = ''
    pin_bar_arr = [] #长度为10
    data_to_insert = []


    for row in result:
        if code == '':
            code = row[0]

        trade_date = row[1]
        open_p = row[2]
        high_p = row[3]
        low_p = row[4]
        close_p = row[5]

        pt = 'N'

        # 单根pin_bar处理
        pin_bar_tag = check_pin_bar(open_p, high_p, low_p, close_p)

        pin_bar_arr.append(row)
        if len(pin_bar_arr) > 8:
            pin_bar_arr.pop(0)

        # 多根pin_bar处理
        if not pin_bar_tag:
            if len(pin_bar_arr) > 1:
                merge_open = pin_bar_arr[-2][2]
                merge_close = close_p
                merge_high = max(pin_bar_arr[-2][3], high_p)
                merge_low = min(pin_bar_arr[-2][4], low_p)
                pin_bar_tag = check_pin_bar(merge_open, merge_high, merge_low, merge_close)
                if not pin_bar_tag:
                    if len(pin_bar_arr) > 2:
                        merge_open_1 = pin_bar_arr[-3][2]
                        merge_close_1 = close_p
                        merge_high_1 = max(pin_bar_arr[-3][3], high_p)
                        merge_low_1 = min(pin_bar_arr[-3][4], pin_bar_arr[-2][4], low_p)
                        pin_bar_tag = check_pin_bar(merge_open_1, merge_high_1, merge_low_1, merge_close_1)
                        if pin_bar_tag:
                            pt = 'P3'
                elif pin_bar_tag:
                    pt = 'P2'
        else:
            pt = 'P1'


        # 获取8根K线的高点 如果当前K为最高点或者离高点的盈亏比为2 则生效
        # highest = max(k[3] for k in pin_bar_arr)
        # if pin_bar_tag and (highest == high_p or (highest - high_p) / (high_p - low_p) >= 2):
        #     pin_bar_tag = True
        # else:
        #     pin_bar_tag = False
        #
        # if not pin_bar_tag:
        #     pt = 'N'

        # 打印结果
        print(
            f"{code} {trade_date} {open_p} {close_p} {high_p} {low_p} {pt}")

        data_to_insert.append((
            code,
            trade_date,
            open_p,
            high_p,
            low_p,
            close_p,
            pt
        ))

    return data_to_insert


def check_all(the_date=20160224, ts_code=None):
    con.execute("""
        DROP TABLE IF EXISTS week_check;
    """)
    if ts_code is None:
        result = con.sql("""
                         select *
                         from weekly
                         where trade_date >= ? and (ts_code like '00%' or ts_code like '60%')
                         order by ts_code, trade_date
                         """, params=[the_date]).fetchall()
    else:
        result = con.sql("""
                         select *
                         from weekly
                         where trade_date >= ? and ts_code = ?
                         order by ts_code, trade_date
                         """, params=[the_date, ts_code]).fetchall()

    grouped_data = {}
    for row in result:
        ts_code = row[0]  # 根据实际表结构调整索引
        if ts_code not in grouped_data:
            grouped_data[ts_code] = []
        grouped_data[ts_code].append(row)

    data_to_insert = []
    for ts_code in grouped_data:
        arr = check(grouped_data[ts_code])
        data_to_insert.extend(arr)

    if len(data_to_insert) > 0:
        df = pd.DataFrame(
            data_to_insert,
            columns=['ts_code', 'trade_date', 'price_open', 'price_high', 'price_low', 'price_close', 'pin_bar_tag']
        )

        df.to_csv('2.csv', index=False)
        con.execute("""
                    CREATE TABLE week_check AS
                    SELECT *
                    FROM read_csv(
                            '2.csv',
                            header = true,
                            delim = ',',
                            quote = '"',
                            escape = '"',
                            nullstr = '',
                            columns = {
                                'ts_code': 'VARCHAR', 'trade_date': 'BIGINT',
                                    'price_open': 'DECIMAL(18,4)',
                                    'price_high': 'DECIMAL(18,4)',
                                    'price_low': 'DECIMAL(18,4)',
                                    'price_close': 'DECIMAL(18,4)',
                                'pin_bar_tag': 'VARCHAR'
                                },
                            auto_detect = false
                         )
                    """)
        #
        # con.register('temp_append', df)
        # con.execute("""
        #              create table week_check as
        #              SELECT *
        #              FROM temp_append
        #              """)


if __name__ == '__main__':
    check_all()
    # check_all()
    # check()
    # print(con.execute("""
    #                   SELECT column_name, data_type
    #                   FROM information_schema.columns
    #                   WHERE table_name = 'week_check'
    #                   ORDER BY ordinal_position
    #                   """).fetchdf())
