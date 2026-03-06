import duckdb
import pandas as pd
import openpyxl

if __name__ == '__main__':
    # 1. 连接 DuckDB (可以是内存或文件)
    con = duckdb.connect('stock.duckdb')

    # 2. 执行查询
    query = """
            SELECT *
            FROM week_check
            WHERE trade_date >= 20260302 and pin_bar_tag in ('P1', 'P2', 'P3') and radio < 0.5
            """
    df = con.execute(query).df()  # 关键：直接转为 DataFrame

    # 3. 导出到 Excel
    output_file = 'kline_data.xlsx'
    df.to_excel(output_file, index=False, sheet_name='Daily Data')

    print(f"成功导出到 {output_file}")