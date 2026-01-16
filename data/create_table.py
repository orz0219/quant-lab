import duckdb

if __name__ == '__main__':
    import duckdb

    con = duckdb.connect('stock.duckdb')

    # 创建表 + 索引
    con.execute("""
               CREATE TABLE IF NOT EXISTS daily (
    ts_code VARCHAR,
    trade_date INTEGER,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    pre_close FLOAT,
    change FLOAT,
    pct_chg FLOAT,
    vol BIGINT,
    amount DOUBLE
);
CREATE INDEX IF NOT EXISTS idx_code_date ON daily(ts_code, trade_date);
                """)

    df = duckdb.sql("""
                    SELECT ts_code,
trade_date,
open,
high,
low,
close,
pre_close,
change,
pct_chg,
vol,
amount
                    FROM '20260115.parquet'
                    """).df()


    # 插入数据（df 是你的 pandas DataFrame）
    con.register('df_input', df)
    con.execute("INSERT INTO daily SELECT * FROM df_input")

    # 查询示例
    result = con.sql("""
                     SELECT trade_date, close, pct_chg
                     FROM daily
                     WHERE ts_code = '000001.SZ'
                     ORDER BY trade_date DESC
                         LIMIT 10
                     """).df()

    print(result)
    con.close()