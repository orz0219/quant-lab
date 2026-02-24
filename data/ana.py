"""
有几个问题
pinBar 如何定义
压力位如何定义
支撑位如何定义
趋势线如何定义 当前趋势如何判断
盈亏比大于2怎么标记
"""
from decimal import Decimal

import duckdb
from decimal import Decimal
from create_table import code_select

# 链接数据库
con = duckdb.connect('stock.duckdb')


def check(d=20050224, code='000001.SZ'):
    result = con.sql("""
                     select *
                     from weekly
                     where trade_date > ?
                       and ts_code = ?
                     order by trade_date
                     """, params=[d, code]).fetchall()
    code = ''
    prev_low = None
    prev_high = None
    prev_trend = None  # 前一个K线的趋势（U:上升, D:下降, None:初始状态）
    up_reversal_count = 0  # 上升反转计数器（D→U）
    down_reversal_count = 0  # 下降反转计数器（U→D）
    last_up_high = None  # 上一次上升反转的high值
    last_down_low = None  # 上一次下降反转的low值
    buy_tag = ''
    last_is_high = False
    last_is_buy = False
    last_buy_price = 0.0
    profit = Decimal('0.00')
    total_profit = Decimal('0.00')

    data_to_insert = []

    for row in result:
        if code == '':
            code = row[0]

        trade_date = row[1]
        price_open = row[2]
        price_high = row[3]
        price_low = row[4]
        price_close = row[5]
        trend = 'U'
        # 处理第一条记录（没有前值）
        if prev_low is None:
            extra_mark = ''
            # 更新前值
            prev_low = price_low
            prev_high = price_high
            prev_trend = trend
            continue

        if last_is_high and price_high > prev_high and not last_is_buy:
            buy_tag = 'BUY'
            last_is_high = False
            last_is_buy = True
            last_buy_price = prev_high + Decimal('0.01')
            profit = (price_high - price_low)
        else:
            buy_tag = ''
            last_is_high = False

        # 计算当前趋势
        current_trend = prev_trend  # 默认为前一个趋势

        # 检查上升趋势条件
        if price_high > prev_high:
            current_trend = 'U'

        # 检查下降趋势条件
        if price_low < prev_low:
            current_trend = 'D'

        # 如果两者都满足，延续前一个趋势
        if price_high > prev_high and price_low < prev_low:
            current_trend = prev_trend

        # 检查趋势反转
        extra_mark = ''
        if prev_trend == 'D' and current_trend == 'U':
            # 上升反转：D→U
            if last_up_high is None:
                # 第一次上升反转
                up_reversal_count = 1
                extra_mark = 'H1'
                last_up_high = price_high
            else:
                # 检查是否需要重置：当前H的high < 之前H的high
                if price_high < last_up_high:
                    # 重置：当前标记为H1，并添加"支撑"标记
                    up_reversal_count = 1
                    extra_mark = 'H1 支撑'
                    last_up_high = price_high  # 更新为当前high
                    last_is_high = True
                else:
                    # 正常递增
                    up_reversal_count += 1
                    extra_mark = f'H{up_reversal_count}'
                    last_up_high = price_high  # 更新为当前high

        elif prev_trend == 'U' and current_trend == 'D':
            # 下降反转：U→D
            if last_down_low is None:
                # 第一次下降反转
                down_reversal_count = 1
                extra_mark = 'L1'
                last_down_low = price_low
            else:
                # 检查是否需要重置：当前L的low > 之前L的low
                if price_low > last_down_low:
                    # 重置：当前标记为L1，并添加"阻力"标记
                    down_reversal_count = 1
                    extra_mark = 'L1 阻力'
                    last_down_low = price_low  # 更新为当前low
                else:
                    # 正常递增
                    down_reversal_count += 1
                    extra_mark = f'L{down_reversal_count}'
                    last_down_low = price_low  # 更新为当前low
        if last_is_buy and buy_tag == '':
            profit_now = prev_low - Decimal('0.01') - last_buy_price
            if profit_now > profit * Decimal(2) and (prev_trend == 'U' and current_trend == 'D'):
                total_profit += profit_now
                buy_tag = 'SELL' + str(profit_now)
                last_is_buy = False
            elif profit_now < -profit:
                total_profit -= (profit + Decimal('0.01'))
                buy_tag = 'SELL' + str(-(profit + Decimal('0.01')))
                last_is_buy = False

        # 打印结果
        # print(
        #     f"{code} {trade_date} {price_open} {price_close} {price_high} {price_low} {current_trend} {extra_mark} {buy_tag}")

        data_to_insert.append((
            code,
            trade_date,
            price_open,
            price_high,
            price_low,
            price_close,
            current_trend,
            extra_mark,
            buy_tag
        ))

        # 更新前值
        prev_low = price_low
        prev_high = price_high
        prev_trend = current_trend

    if data_to_insert:
        con.executemany(f"""
                INSERT INTO week_check 
                (ts_code, trade_date, price_open, price_high, price_low, price_close, 
                 current_trend, extra_mark, buy_tag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
        print(f"成功将 {len(data_to_insert)} 条 {code} 回测结果存入 week_check 表中。")
    else:
        print("没有数据需要存储。")


if __name__ == '__main__':
    con.execute("""
        truncate table week_check;
    """)
    code_list = code_select()
    for code in code_list:
        check(code=code)