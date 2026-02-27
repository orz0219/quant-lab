import duckdb
from PIL import Image, ImageDraw, ImageFont


def text_to_image(text, output_path,  # 白色
                  width=None,
                  height=None):
    """
    将文字生成为图片

    参数:
    text (str): 要生成的文本
    output_path (str): 输出图片的路径
    font_size (int): 字体大小
    text_color (tuple): 文字颜色(RGB)
    bg_color (tuple): 背景颜色(RGB)
    width (int): 图片宽度（可选）
    height (int): 图片高度（可选）
    font_path (str): 字体文件路径（可选，用于支持中文）
    """
    text_color = (0, 0, 0) # 黑色
    bg_color = (255, 255, 255)
    font = ImageFont.truetype('arial.ttf', 72)

    # 计算文本尺寸
    bbox = font.getbbox(text)
    text_width, text_height = width, height

    # 如果未指定尺寸，使用文本尺寸
    if width is None:
        width = text_width + 20  # 添加边距
    if height is None:
        height = text_height + 20

    # 创建背景图片
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 文本居中
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    # 绘制文字
    draw.text((text_x, text_y), text, fill=text_color, font=font)

    # 保存图片
    img.save(output_path)
    print(f"图片已保存至: {output_path}")
    return img


# 使用示例
if __name__ == "__main__":
    # 中英文混合示例
    con = duckdb.connect('stock.duckdb')
    result = con.sql("""
        select ts_code from week_check where trade_date >= 20260209 and  buy_tag = 'BUY'
    """).fetchall()

    text = ""
    for row in result:
        text += (row[0] + '\n')
        print(row[0])
    # 保存路径
    output_path = "text_to_image.png"

    # 生成图片（使用默认字体）
    text_to_image(text, output_path, width=400, height=72 * len(result))

    # 或者指定中文字体路径（Windows示例）
    # text_to_image(text, output_path, font_size=32,
    #               font_path='C:/Windows/Fonts/simhei.ttf')

    print("生成完成！")