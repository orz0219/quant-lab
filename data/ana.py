"""
基于pinBar的周线交易系统

pinBar的定义
下影线长度通常≥（实体+上影线）2倍

pinBar的合并
可以最多由3根K线组成
"""
from decimal import Decimal, getcontext

import duckdb
import pandas as pd

# 链接数据库
con = duckdb.connect('stock.duckdb')

getcontext().prec = 4


def get_lower_shadow_range(kline):
    o = Decimal(str(kline['open_p']))
    c = Decimal(str(kline['close_p']))
    l = Decimal(str(kline['low_p']))

    # 下影线底部永远是 low
    bottom = l
    # 下影线顶部是 open 和 close 中较小的那个
    top = min(o, c)

    return bottom, top

def calculate_lower_shadow_overlap(current_k, prev_k):
    """
    计算当前K线下影线与前一根K线整体区间的重叠度
    返回重叠部分占当前下影线长度的比例 (0.0 ~ 1.0)
    """
    # 1. 获取当前K线下影线区间
    curr_shadow_bottom, curr_shadow_top = get_lower_shadow_range(current_k)
    curr_shadow_len = curr_shadow_top - curr_shadow_bottom

    # 2. 获取前一根K线的整体区间
    prev_low = prev_k[4]
    prev_high = prev_k[3]

    # 3. 计算重叠部分
    # 重叠区的上界 = min(当前下影线顶, 前K线高)
    overlap_top = min(curr_shadow_top, prev_high)
    # 重叠区的下界 = max(当前下影线底, 前K线低)
    overlap_bottom = max(curr_shadow_bottom, prev_low)

    overlap_len = overlap_top - overlap_bottom

    # 如果没有重叠
    if overlap_len <= 0:
        return Decimal('0')

    # 4. 计算比例 (重叠长度 / 当前下影线总长度)
    ratio = overlap_len / curr_shadow_len

    # 限制最大值为 1 (防止浮点误差或逻辑极端情况)
    return min(ratio, Decimal('1'))


def check_pin_bar(open_p, high_p, low_p, close_p):
    rr_ratio = Decimal(2)  # 盈亏比设定
    pin_bar_tag = False
    if high_p == low_p:
        pin_bar_tag = False
    elif close_p >= open_p:
        if close_p == open_p:
            if high_p == open_p:
                pin_bar_tag = True
        else:
            pin_bar_tag = (open_p - low_p) / (high_p - open_p) >= 2.5
    else:
        pin_bar_tag = (close_p - low_p) / (high_p - close_p) >= 2.5
    if pin_bar_tag:
        return {
            'open_p': open_p,
            'high_p': high_p,
            'low_p': low_p,
            'close_p': close_p,
            'win_p': high_p + (high_p - low_p) * rr_ratio,
            'lose_p': low_p - Decimal(0.01),
            'status': 'Open'
        }
    else: return None


def check(result):
    code = ''
    pin_bar_arr = [] #长度为10
    data_to_insert = []
    active_trade = None

    for row in result:
        if code == '':
            code = row[0]

        trade_date = row[1]
        open_p = row[2]
        high_p = row[3]
        low_p = row[4]
        close_p = row[5]

        pt = 'N'

        if trade_date == 20260302:
            print(1)

        near_high = high_p
        if len(pin_bar_arr) > 1:
            near_high = max(pin_bar_arr, key=lambda x: x[3])[3]

        #计算上一个pin_bar是否发生了买入
        tag_win = False
        tag_lose = False
        if active_trade is not None:
            if (active_trade['high_p'] < high_p < active_trade['win_p'] and not active_trade['status'] == 'HOLD'
                    and near_high > active_trade['high_p'] * Decimal(2)):
                #计算8周内是否出现2倍盈亏比的高点
                active_trade['status'] = 'HOLD'
                pt = 'BUY'
            if active_trade['status'] == 'HOLD':
                if high_p > active_trade['win_p']:
                    tag_win = True
                    active_trade = None
                if active_trade is not None and low_p < active_trade['lose_p']:
                    tag_lose = True
                    active_trade = None
            else:
                active_trade = None

        pin_bar_arr.append(row)
        if len(pin_bar_arr) > 8:
            pin_bar_arr.pop(0)

        if active_trade is None and not tag_win and not tag_lose:
            # 单根pin_bar处理
            active_trade = check_pin_bar(open_p, high_p, low_p, close_p)

            # 多根pin_bar处理
            if active_trade is None:
                if len(pin_bar_arr) > 1:
                    merge_open = pin_bar_arr[-2][2]
                    merge_close = close_p
                    merge_high = max(pin_bar_arr[-2][3], high_p)
                    merge_low = min(pin_bar_arr[-2][4], low_p)
                    active_trade = check_pin_bar(merge_open, merge_high, merge_low, merge_close)
                    if active_trade is None:
                        if len(pin_bar_arr) > 2:
                            p3 = pin_bar_arr[-3]
                            p2 = pin_bar_arr[-2]
                            merge_open_1 = p3[2]  # 通常取第一根的开盘
                            merge_close_1 = close_p
                            merge_high_1 = max(p3[3], p2[3], high_p)
                            merge_low_1 = min(p3[4], p2[4], low_p)
                            active_trade = check_pin_bar(merge_open_1, merge_high_1, merge_low_1, merge_close_1)
                            if active_trade is not None:
                                pt = 'P3'
                    else:
                        pt = 'P2'
            else:
                pt = 'P1'
        else:
            if tag_win:
                pt = 'WIN'
            elif tag_lose:
                pt = 'LOSE'

        # 添加pin bar重合度校验
        ratio = Decimal(0)
        if pt == 'P1' and len(pin_bar_arr) > 1:
            for i in range(len(pin_bar_arr) - 1):
                r = pin_bar_arr[i]
                ratio += calculate_lower_shadow_overlap(active_trade, r)
            ratio = ratio / Decimal(len(pin_bar_arr) - 1)
        elif pt == 'P2' and len(pin_bar_arr) > 2:
            for i in range(len(pin_bar_arr) - 2):
                r = pin_bar_arr[i]
                ratio += calculate_lower_shadow_overlap(active_trade, r)
            ratio = ratio / Decimal(len(pin_bar_arr) - 2)
        elif pt == 'P3' and len(pin_bar_arr) > 3:
            for i in range(len(pin_bar_arr) - 3):
                r = pin_bar_arr[i]
                ratio += calculate_lower_shadow_overlap(active_trade, r)
            ratio = ratio / Decimal(len(pin_bar_arr) - 3)

        # if ratio > 0.382:
        #     active_trade = None
        #     pt = 'N'

        win_p = Decimal(0)
        lose_p = Decimal(0)
        if active_trade is not None:
            win_p = active_trade['win_p']
            lose_p = active_trade['lose_p']
        # 打印结果
        if pt != 'N':
            print(
                f"{code} {trade_date} {open_p} {close_p} {high_p} {low_p} {pt} {ratio} {win_p} {lose_p} {near_high}")

        data_to_insert.append((
            code,
            trade_date,
            open_p,
            high_p,
            low_p,
            close_p,
            pt,
            ratio,
            win_p,
            lose_p,
            near_high
        ))

    return data_to_insert


def check_all(the_date=20160101, ts_code=None):
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
        print(len(data_to_insert))
        df = pd.DataFrame(
            data_to_insert,
            columns=['ts_code', 'trade_date', 'price_open', 'price_high', 'price_low', 'price_close', 'pin_bar_tag', 'radio', 'win_p', 'lose_p', 'near_high']
        )

        df.to_csv('2.csv', index=False)
        con.execute("""
                    DROP TABLE IF EXISTS week_check;
                    """)
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
                                'ts_code': 'VARCHAR',
                                'trade_date': 'BIGINT',
                                    'price_open': 'DECIMAL(18,4)',
                                    'price_high': 'DECIMAL(18,4)',
                                    'price_low': 'DECIMAL(18,4)',
                                    'price_close': 'DECIMAL(18,4)',
                                'pin_bar_tag': 'VARCHAR',
                                'radio':'DECIMAL(18,4)',
                                'win_p': 'DECIMAL(18,4)',
                                'lose_p': 'DECIMAL(18,4)',
                                'near_high': 'DECIMAL(18,4)',
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

def select_today():
    codes = con.sql("""
        select ts_code from week_check where trade_date = 20260302 and pin_bar_tag != 'N'
            and ts_code not in (select ts_code from week_check where trade_date = 20260224 and pin_bar_tag != 'N')
    """).fetchall()
    for code in codes:
        print(code[0])


if __name__ == '__main__':
    check_all()
    # select_today()
    # check_all(ts_code='603665.SH')
    # check()
    # print(con.execute("""
    #                   SELECT column_name, data_type
    #                   FROM information_schema.columns
    #                   WHERE table_name = 'week_check'
    #                   ORDER BY ordinal_position
    #                   """).fetchdf())
