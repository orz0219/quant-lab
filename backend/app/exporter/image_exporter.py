"""图像导出工具。"""
import os

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

from app.core.database import DuckDBPool


class ImageExporter:
    def __init__(self, db: DuckDBPool):
        self.db = db

    def export_from_codes(self, codes: list[str], output_path: str, title: str = "信号股票") -> int:
        if not codes:
            return 0
        if not _PIL_AVAILABLE:
            raise ImportError("Pillow 未安装。请先 pip install Pillow。")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        width = 800
        line_height = 40
        height = max(200, line_height * (len(codes) + 2))

        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
        except Exception:
            font = ImageFont.load_default()

        draw.text((20, 20), title, fill="black", font=font)

        for i, code in enumerate(codes):
            y = 80 + i * line_height
            draw.text((20, y), f"{i + 1}. {code}", fill="black", font=font)

        img.save(output_path)
        return len(codes)
