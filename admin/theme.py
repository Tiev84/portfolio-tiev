# -*- coding: utf-8 -*-
"""
theme.py — màu sắc, chữ và bố cục của TOÀN BỘ website.

Giá trị nằm ở admin/theme.json, từ đó sinh ra css/theme.css. File css này được
nạp ĐẦU TIÊN trong mọi trang, nên đổi một chỗ là cả web đổi theo.

Đừng sửa tay css/theme.css — mở app, vào mục "Giao diện" rồi bấm lưu.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = HERE / "theme.json"
OUTPUT = REPO / "css" / "theme.css"

# Nhãn tiếng Việt + nhóm, dùng để dựng giao diện chỉnh trong app.
# (token, nhãn, nhóm, mô tả)
COLOR_FIELDS = [
    ("bg", "Nền trang", "Nền", "Màu nền chính của mọi trang"),
    ("footer-bg", "Nền chân trang", "Nền", "Cũng dùng cho menu điện thoại"),
    ("surface-light", "Nền khối sáng", "Nền", "Khung ảnh, bảng khách hàng"),
    ("accent", "Màu nhấn", "Nhấn", "Màu vàng thương hiệu: nút, tiêu đề chân trang"),
    ("accent-hover", "Màu nhấn khi rê chuột", "Nhấn", ""),
    ("accent-dim", "Màu nhấn nhạt", "Nhấn", "Viền trang trí"),
    ("on-accent", "Chữ trên màu nhấn", "Nhấn", "Chữ nằm trên nút vàng"),
    ("text", "Chữ chính", "Chữ", "Tiêu đề, nội dung chính"),
    ("text-strong", "Chữ nổi bật", "Chữ", "Email chân trang"),
    ("text-soft", "Chữ dịu", "Chữ", "Danh sách kỹ năng"),
    ("text-body", "Chữ đoạn văn", "Chữ", "Mô tả, giới thiệu"),
    ("text-quiet", "Chữ mờ", "Chữ", "Mô tả trong trang chi tiết"),
    ("text-dim", "Chữ mờ hơn", "Chữ", "Menu điều hướng"),
    ("text-muted", "Chữ mờ nhất", "Chữ", "Danh mục, mạng xã hội"),
    ("border", "Viền", "Viền", ""),
    ("border-soft", "Viền nhạt", "Viền", ""),
    ("border-strong", "Viền đậm", "Viền", ""),
]

DEFAULTS = {
    "colors": {
        "bg": "#1b1b1b",
        "footer-bg": "#111111",
        "surface-light": "#ffffff",
        "accent": "#ffda24",
        "accent-hover": "#e1bd00",
        "accent-dim": "#d5b600",
        "on-accent": "#151515",
        "text": "#f7f7f7",
        "text-strong": "#ffffff",
        "text-soft": "#dddddd",
        "text-body": "#d1d1d1",
        "text-quiet": "#c9c9c9",
        "text-dim": "#aaaaaa",
        "text-muted": "#969696",
        "border": "#666666",
        "border-soft": "#555555",
        "border-strong": "#333333",
    },
    "font": {
        "family": "Montserrat",
        "fallback": "Arial, sans-serif",
    },
    "layout": {
        "container": 850,  # bề ngang tối đa của nội dung (px)
        "radius": 8,  # bo góc chung (px)
        "card_radius": 7,  # bo góc thẻ project (px)
        "grid_col_gap": 18,  # khoảng cách ngang giữa các thẻ (px)
        "grid_row_gap": 31,  # khoảng cách dọc (px)
        "card_ratio": "1 / 1",  # tỉ lệ khung ảnh thẻ nhỏ
        # Thẻ lớn: đúng tỉ lệ file gốc 4500x3519 để ảnh không bị cắt
        "card_ratio_wide": "4500 / 3519",
        "card_ratio_mobile": "1.55 / 1",  # thẻ nhỏ khi xem trên điện thoại
    },
    "grid": {
        # Bố cục lặp: mỗi khối gồm 2 thẻ lớn rồi 3 thẻ nhỏ.
        "auto_pattern": True,
        "wide_per_block": 2,
        "narrow_per_block": 3,
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load() -> dict:
    if CONFIG.exists():
        try:
            return _merge(DEFAULTS, json.loads(CONFIG.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return json.loads(json.dumps(DEFAULTS))


def save(data: dict) -> dict:
    merged = _merge(DEFAULTS, data or {})
    CONFIG.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return merged


def block_size(cfg: dict | None = None) -> int:
    grid = (cfg or load())["grid"]
    return max(1, int(grid["wide_per_block"]) + int(grid["narrow_per_block"]))


def is_wide(index: int, cfg: dict | None = None) -> bool:
    """index tính từ 0. Hai thẻ đầu mỗi khối là thẻ lớn."""
    grid = (cfg or load())["grid"]
    wide = max(0, int(grid["wide_per_block"]))
    size = block_size(cfg)
    return (index % size) < wide


def render(cfg: dict | None = None) -> str:
    cfg = cfg or load()
    colors = cfg["colors"]
    font = cfg["font"]
    layout = cfg["layout"]

    lines = [
        "/* =========================================================",
        "   File này được TẠO TỰ ĐỘNG bởi admin app (admin/theme.py).",
        "   Đừng sửa tay — mở app, vào mục Giao diện rồi bấm lưu.",
        "",
        "   Nạp đầu tiên trong mọi trang, nên sửa ở đây là cả web đổi.",
        "   ========================================================= */",
        "",
        ":root {",
    ]

    group = None
    for token, _label, section, _hint in COLOR_FIELDS:
        if section != group:
            lines.append("")
            group = section
        lines.append(f"  --{token}: {colors.get(token, DEFAULTS['colors'][token])};")

    stack = f'"{font["family"]}", {font["fallback"]}'.strip().rstrip(",")
    lines += [
        "",
        f"  --font-main: {stack};",
        "",
        f"  --container: {layout['container']}px;",
        f"  --radius: {layout['radius']}px;",
        f"  --card-radius: {layout['card_radius']}px;",
        f"  --grid-col-gap: {layout['grid_col_gap']}px;",
        f"  --grid-row-gap: {layout['grid_row_gap']}px;",
        f"  --card-ratio: {layout['card_ratio']};",
        f"  --card-ratio-wide: {layout['card_ratio_wide']};",
        f"  --card-ratio-mobile: {layout['card_ratio_mobile']};",
        "",
        "  /* Tên cũ, giữ lại cho css sẵn có khỏi gãy */",
        "  --yellow: var(--accent);",
        "}",
        "",
    ]
    return "\n".join(lines)


def build() -> dict:
    cfg = load()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(cfg), encoding="utf-8")
    return {"theme": str(OUTPUT.relative_to(REPO)), "colors": len(cfg["colors"])}


if __name__ == "__main__":
    print(build())
