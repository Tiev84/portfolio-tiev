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
        # Bề ngang ảnh trong trang chi tiết (%). Mọi ảnh dùng chung số này
        # nên mép trái - phải luôn thẳng hàng.
        "gallery_width": 100,
        "card_title_size": 16,  # cỡ chữ tên project dưới thẻ (px)
        "card_category_size": 10,  # cỡ chữ dòng danh mục (px)
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


# ----------------------------------------------------------------------
# Màu chủ đạo
#
# Màu vàng của web không phải một màu, mà là một BỘ bốn màu ăn khớp nhau:
# màu nhấn, màu khi rê chuột (đậm hơn), viền nhạt, và màu chữ nằm trên nền
# đó. Đổi tay từng cái thì gần như chắc chắn lệch tông.
#
# Nên ở đây chỉ nhận MỘT màu rồi tự suy ra ba màu còn lại, giữ đúng quan hệ
# sáng - tối như bộ vàng gốc.
# ----------------------------------------------------------------------

# Độ sáng của accent-hover và accent-dim so với accent, đo từ bộ vàng gốc
# (#ffda24 -> #e1bd00 -> #d5b600). Tính ngay tại đây để nếu sau này đổi
# DEFAULTS thì quan hệ vẫn tự khớp theo.
def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    # Kiểm tra cả độ dài lẫn ký tự ở đây, để lỗi báo ra bằng tiếng Việt
    # thay vì câu tiếng Anh khó hiểu của hàm int().
    if len(v) != 6 or any(c not in "0123456789abcdefABCDEF" for c in v):
        raise ValueError(f"“{value}” không phải mã màu. Phải có dạng #rrggbb, ví dụ #ffda24.")
    return tuple(int(v[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def _rgb_to_hsl(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (c / 255 for c in rgb)
    hi, lo = max(r, g, b), min(r, g, b)
    light = (hi + lo) / 2
    if hi == lo:
        return 0.0, 0.0, light
    d = hi - lo
    sat = d / (2 - hi - lo) if light > 0.5 else d / (hi + lo)
    if hi == r:
        hue = ((g - b) / d) % 6
    elif hi == g:
        hue = (b - r) / d + 2
    else:
        hue = (r - g) / d + 4
    return hue / 6, sat, light


def _hsl_to_rgb(h: float, s: float, light: float) -> tuple[float, float, float]:
    if s == 0:
        return (light * 255,) * 3
    q = light * (1 + s) if light < 0.5 else light + s - light * s
    p = 2 * light - q

    def kenh(t: float) -> float:
        t = t % 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    return tuple(kenh(h + k) * 255 for k in (1 / 3, 0, -1 / 3))  # type: ignore[return-value]


def _luminance(rgb: tuple[int, int, int]) -> float:
    """Độ sáng cảm nhận theo chuẩn WCAG, để chọn chữ đen hay chữ trắng."""

    def tuyen_tinh(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (tuyen_tinh(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """Tỉ lệ tương phản giữa hai màu. Chữ dễ đọc cần từ 4.5 trở lên."""
    la, lb = _luminance(_hex_to_rgb(a)), _luminance(_hex_to_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


_L_GOC = _rgb_to_hsl(_hex_to_rgb(DEFAULTS["colors"]["accent"]))[2]
TI_LE_HOVER = _rgb_to_hsl(_hex_to_rgb(DEFAULTS["colors"]["accent-hover"]))[2] / _L_GOC
TI_LE_DIM = _rgb_to_hsl(_hex_to_rgb(DEFAULTS["colors"]["accent-dim"]))[2] / _L_GOC


ACCENT_TOKENS = ("accent", "accent-hover", "accent-dim", "on-accent")


def accent_family(value: str) -> dict:
    """
    Từ một màu, dựng đủ bộ bốn màu nhấn.

    Màu sáng thì rê chuột sẽ tối đi (như bộ vàng gốc). Nhưng màu tối mà tối
    thêm nữa thì gần như không thấy khác gì, nên đổi chiều: sáng lên, lệch
    đúng bằng chừng đó.
    """
    hue, sat, light = _rgb_to_hsl(_hex_to_rgb(value))

    if light > 0.5:
        l_hover, l_dim = light * TI_LE_HOVER, light * TI_LE_DIM
    else:
        l_hover = light + (1 - light) * (1 - TI_LE_HOVER)
        l_dim = light + (1 - light) * (1 - TI_LE_DIM)

    accent = _rgb_to_hex(_hsl_to_rgb(hue, sat, light))
    # Chữ trên nền màu nhấn: chọn bên nào đọc rõ hơn, không đoán mò
    den, trang = DEFAULTS["colors"]["on-accent"], "#ffffff"
    on_accent = den if contrast(accent, den) >= contrast(accent, trang) else trang

    return {
        "accent": accent,
        "accent-hover": _rgb_to_hex(_hsl_to_rgb(hue, sat, l_hover)),
        "accent-dim": _rgb_to_hex(_hsl_to_rgb(hue, sat, l_dim)),
        "on-accent": on_accent,
    }


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
        f"  --gallery-width: {layout['gallery_width']}%;",
        f"  --card-title-size: {layout['card_title_size']}px;",
        f"  --card-category-size: {layout['card_category_size']}px;",
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
