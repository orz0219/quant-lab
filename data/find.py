"""
周线形态分析
"""
import duckdb

# 链接数据库
con = duckdb.connect('stock.duckdb')

if __name__ == '__main__':
    data_list = con.sql("""
    select trade_date from weekly
        order by ts_code, trade_date desc
    """).fetchall()

    for data in data_list:
        print(data[0])