# -*- coding: utf-8 -*-
"""
make_icon.py — tạo icon cho app từ logo trong assets/icons/.

Sinh ra:
    admin/ui/icon.png              1024x1024, nguồn chung cho mọi hệ điều hành
    admin/ui/app.ico               icon cho shortcut trên Windows
    assets/icons/favicon.ico       icon trên tab trình duyệt (16/32/48)
    assets/icons/favicon-192.png   icon cho trình duyệt đời mới
    assets/icons/apple-touch-icon.png  icon khi lưu web ra màn hình iPhone

App và website dùng CHUNG một icon — sửa logo thì chạy lại file này là cả hai
cùng đổi theo.

Trên macOS, install-mac.command sẽ tự đổi icon.png thành .icns.

    py -3 admin/make_icon.py
"""

from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SVG = REPO / "assets" / "icons" / "logo.svg"
PNG = REPO / "assets" / "icons" / "logo.png"
OUT_PNG = HERE / "ui" / "icon.png"
OUT_ICO = HERE / "ui" / "app.ico"

WEB_ICONS = REPO / "assets" / "icons"
OUT_FAVICON = WEB_ICONS / "favicon.ico"
OUT_FAVICON_PNG = WEB_ICONS / "favicon-192.png"
OUT_APPLE = WEB_ICONS / "apple-touch-icon.png"

SIZE = 1024
BG = (27, 27, 27, 255)  # #1b1b1b, nền tối giống website
RADIUS = int(SIZE * 0.22)  # bo góc kiểu icon macOS
LOGO_WIDTH_RATIO = 0.58


def load_logo():
    """
    logo.svg chỉ là một ảnh bitmap 2550px nhúng base64 — lấy nó ra thì icon
    nét hơn nhiều so với logo.png (chỉ 99px).
    """
    from PIL import Image

    if SVG.is_file():
        match = re.search(
            r'xlink:href="data:image/(?:png|jpeg);base64,([^"]+)"',
            SVG.read_text(encoding="utf-8"),
        )
        if match:
            raw = base64.b64decode(match.group(1))
            return Image.open(io.BytesIO(raw)).convert("RGBA")

    if PNG.is_file():
        return Image.open(PNG).convert("RGBA")

    sys.exit(f"Không thấy logo ở {SVG} hoặc {PNG}")


def main() -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        sys.exit("Cần Pillow. Cài bằng:  py -3 -m pip install Pillow")

    logo = load_logo()
    box = logo.getbbox()  # cắt bỏ viền trong suốt thừa
    if box:
        logo = logo.crop(box)

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), RADIUS, fill=255)
    canvas.paste(Image.new("RGBA", (SIZE, SIZE), BG), (0, 0), mask)

    target_w = int(SIZE * LOGO_WIDTH_RATIO)
    target_h = max(1, round(logo.height * target_w / logo.width))
    logo = logo.resize((target_w, target_h), Image.LANCZOS)
    canvas.alpha_composite(logo, ((SIZE - target_w) // 2, (SIZE - target_h) // 2))

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_PNG, "PNG")
    canvas.save(
        OUT_ICO,
        "ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    # ---- Icon cho tab trình duyệt, cùng một hình với app ----
    WEB_ICONS.mkdir(parents=True, exist_ok=True)

    canvas.save(
        OUT_FAVICON, "ICO", sizes=[(16, 16), (32, 32), (48, 48)]
    )
    canvas.resize((192, 192), Image.LANCZOS).save(OUT_FAVICON_PNG, "PNG")

    # iOS bo góc giúp rồi nên nền phải kín, không để trong suốt ở góc
    apple = Image.new("RGB", (SIZE, SIZE), BG[:3])
    apple.paste(canvas, (0, 0), canvas)
    apple.resize((180, 180), Image.LANCZOS).save(OUT_APPLE, "PNG")

    for path in (OUT_PNG, OUT_ICO, OUT_FAVICON, OUT_FAVICON_PNG, OUT_APPLE):
        print(f"OK  {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
