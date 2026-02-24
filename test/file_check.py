import json
import re
from pathlib import Path
import duckdb
import pandas as pd


def safe_read_file(file_path: Path, encoding='utf-8') -> str:
    '''
    安全读取文件内容，若失败则返回空字符串或错误提示
    '''
    try:
        return file_path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        # 尝试其他编码（如 GBK，适用于中文 Windows 环境）
        try:
            return file_path.read_text(encoding='gbk')
        except Exception:
            return '[ERROR: Unable to decode file content]'
    except Exception as e:
        return f'[ERROR: {str(e)}]'


def file_check():
    # 获取指定目录下所有文件（递归）
    directory = Path('C:\\Users\\51330\\IdeaProjects')
    all_files = [f for f in directory.rglob('*') if
                 f.is_file() and (f.name.endswith('.java') or f.name.endswith('.xml')) and 'target' not in str(f)]

    data = []
    # 打印所有文件路径
    for file in all_files:
        content = safe_read_file(file)

        imports = []
        # 匹配: import com.example.ClassName;
        pattern = r'import\s+([a-zA-Z_][\w.]*)'
        for line in content.splitlines():
            match = re.match(pattern, line)
            if match:
                full_class = match.group(1)
                if full_class.startswith('com.lenovo.scc'):
                    print(full_class)
                    imports.append(full_class)
        data.append({
            'file_path': str(file),  # 完整路径（字符串）
            'file_name': file.name,  # 仅文件名（如 'MyClass.java'）
            'file_content': content,
            'file_imports': json.dumps(imports)
        })
        if len(imports) > 0:
            print(imports)
    df = pd.DataFrame(data)
    con = duckdb.connect('C:\\Users\\51330\\PycharmProjects\\tvp\\data\\stock.duckdb')
    con.register('df_input', df)
    con.execute("CREATE TABLE java AS SELECT * FROM df_input")
    con.commit()
    con.close()

if __name__ == '__main__':
    con = duckdb.connect('C:\\Users\\51330\\PycharmProjects\\tvp\\data\\stock.duckdb')
    result = con.sql("""
                    select file_name, file_imports, file_content from java where file_name like '%MailV2ServiceImpl%'
                    """).fetchall()

    for row in result:
        print("当前文件是")
        print(row[0])
        print("它的内容是")
        print(row[2])
        print("涉及的其他文件有")
        for p in json.loads(row[1]):
            print(p)
            file_path = '%' + p.split('.')[-1] + '%'
            path = con.sql("""
                    select file_path
                    from java
                    where file_name like ?
                    """, params=[file_path]).fetchone()
            content = safe_read_file(Path(path[0]))
            print(content)
            # 相关的Mapper


