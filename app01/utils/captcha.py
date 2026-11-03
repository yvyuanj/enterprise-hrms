"""图片验证码生成。

使用 Pillow 生成随机 4 位验证码，加入干扰线/噪点，并把答案写入 session，
前端点击图片可刷新（URL 加随机参数绕过缓存）。
"""
import io
import random
import string

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# 去除易混淆字符（0/O、1/l/I）
_CODE_SOURCE = string.digits + 'ABCDEFGHJKLMNPQRSTUVWXYZ'


def gen_code_text(length=4):
    """生成随机验证码文本。"""
    return ''.join(random.choices(_CODE_SOURCE, k=length))


def _load_font(size):
    """优先加载系统字体，失败则退化为默认字体。"""
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def build_captcha_image(text):
    """根据验证码文本绘制图片，返回 PNG 字节流。"""
    width, height = 130, 42
    image = Image.new('RGB', (width, height), (240, 244, 248))
    draw = ImageDraw.Draw(image)
    font = _load_font(32)

    # 随机干扰线
    for _ in range(4):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=self_random_color(), width=2)

    # 随机噪点
    for _ in range(120):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        draw.point((x, y), fill=self_random_color())

    # 逐字符绘制，带轻微偏移与旋转
    char_w = width // (len(text) + 1)
    for i, ch in enumerate(text):
        color = self_random_color(dark=True)
        x = char_w // 2 + i * char_w + random.randint(-4, 4)
        y = random.randint(4, 10)
        draw.text((x, y), ch, font=font, fill=color)

    # 轻微模糊，增加机器识别难度
    image = image.filter(ImageFilter.SMOOTH)

    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()


def self_random_color(dark=False):
    """随机颜色；dark=True 取深色以便识别。"""
    if dark:
        return (random.randint(20, 120), random.randint(20, 120), random.randint(20, 120))
    return (random.randint(120, 200), random.randint(120, 200), random.randint(120, 200))
