# -*- coding: utf-8 -*-
"""
home.py — nội dung trang chủ (index.html).

Chữ nghĩa nằm ở admin/home.json, ảnh nằm trong assets/home/<khung>/ — cùng
kiểu tổ chức thư mục như project: bỏ ảnh vào thư mục, chọn cái nào đang dùng.

Từ đó sinh lại phần giữa HOME:START và HOME:END trong index.html.
Đừng sửa tay phần đó — mở app, vào mục Trang chủ rồi bấm lưu.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import store
import webimg

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = HERE / "home.json"
PAGE = REPO / "index.html"

HOME_DIR = REPO / "assets" / "home"
SLOT_META = "_slot.json"

START = "<!-- HOME:START — tự động tạo bởi admin app, đừng sửa tay -->"
END = "<!-- HOME:END -->"

# Hai khung ảnh trên trang chủ. folder = thư mục trên máy.
SLOTS = [
    {
        "key": "portrait",
        "folder": "chan-dung",
        "label": "Ảnh chân dung",
        "where": "Phần Giới thiệu, bên phải đoạn văn",
        "fallback": "assets/images/avt.jpg",
    },
    {
        "key": "clients",
        "folder": "khach-hang",
        "label": "Ảnh khách hàng",
        "where": "Phần Doanh nghiệp & khách hàng",
        "fallback": "assets/images/client.jpg",
    },
]

DEFAULTS = {
    "sections": ["hero", "about", "skills", "clients"],
    "hidden": [],
    "hero": {
        "title": "TRAN QUOC TIEN",
        "subtitle_left": "Middle Graphics Designer",
        "subtitle_right": "HCMC",
        "button_text": "PORTFOLIO CỦA TÔI",
        "button_href": "portfolio.html",
    },
    "about": {
        "heading": "GIỚI THIỆU",
        "text": (
            "Với hơn 3 năm kinh nghiệm trong môi trường doanh nghiệp và freelance, Tiến "
            "chuyên biến mọi ý tưởng thành sản phẩm thị giác sắc nét, kết hợp linh hoạt "
            "giữa tư duy thiết kế hiện đại, công cụ đồ họa chuyên sâu và công nghệ AI đột "
            "phá. Tiến mang đến giải pháp toàn diện trên đa dạng hạng mục - từ Social Post, "
            "Landing Page đến Bộ nhận diện thương hiệu và Ấn phẩm in ấn POSM - giúp nâng "
            "tầm hình ảnh và tối ưu hiệu quả kinh doanh cho thương hiệu."
        ),
        "button_text": "XEM CV CỦA TÔI",
        "button_href": (
            "https://drive.google.com/drive/folders/1FXwv94fa-MgsUwXDPa-eKa-_119VTg0N"
        ),
        "image_alt": "Trần Quốc Tiến",
    },
    "skills": {
        "heading": "KỸ NĂNG CHUYÊN MÔN",
        "items": [
            {"icon": "graphics.svg", "text": "2D Graphics Design"},
            {"icon": "uiux.svg", "text": "UI/UX Design"},
            {"icon": "posm.svg", "text": "POSM Design"},
            {
                "icon": "ooh.svg",
                "text": "Thiết kế in ấn khổ lớn (OOH, Backdrop, Sign, Photobooth...)",
            },
            {
                "icon": "gpt.svg",
                "text": "Ứng dụng AI: Claude, ChatGPT, Gemini, Flow, Magnific Workflow",
            },
            {"icon": "ps.svg", "text": "Photoshop"},
            {"icon": "ai.svg", "text": "Illustrator"},
            {"icon": "figma.svg", "text": "Figma"},
            {"icon": "capcut.svg", "text": "Capcut"},
        ],
    },
    "clients": {
        "heading": "DOANH NGHIỆP\n& KHÁCH HÀNG\nĐÃ CỘNG TÁC",
        "text": (
            "Tiến đã có kinh nghiệm hợp tác cùng nhiều thương hiệu và đối tác đa dạng, từ "
            "các thương hiệu như Droppii, Bệnh viện Tâm Anh, Điền Quân Network, Fujiwa, "
            "Liên đoàn Thương mại và Công nghiệp Việt Nam VCCI cho đến các thương hiệu F&B "
            "trong và ngoài nước, những khách hàng cá nhân,... Nhờ khả năng linh hoạt theo "
            "từng ngành nghề, Tiến luôn mang đến những thiết kế vừa vặn, đúng gu và hiệu "
            "quả cho từng dự án."
        ),
        "image_alt": "Doanh nghiệp và khách hàng đã cộng tác",
    },
}

SECTION_LABELS = {
    "hero": "Tên & nghề",
    "about": "Giới thiệu",
    "skills": "Kỹ năng chuyên môn",
    "clients": "Doanh nghiệp & khách hàng",
}


# ----------------------------------------------------------------------
# Cấu hình
# ----------------------------------------------------------------------


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
    # chỉ giữ tên section hợp lệ, tránh sinh HTML rác
    merged["sections"] = [s for s in merged["sections"] if s in SECTION_LABELS] or list(
        DEFAULTS["sections"]
    )
    merged["hidden"] = [s for s in merged["hidden"] if s in SECTION_LABELS]
    CONFIG.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return merged


# ----------------------------------------------------------------------
# Khung ảnh (mỗi khung là một thư mục, giống project)
# ----------------------------------------------------------------------


def slot_dir(key: str) -> Path:
    spec = next((s for s in SLOTS if s["key"] == key), None)
    if spec is None:
        raise ValueError(f"Không có khung ảnh “{key}”")
    return HOME_DIR / spec["folder"]


def read_slot(spec: dict) -> dict:
    folder = HOME_DIR / spec["folder"]
    folder.mkdir(parents=True, exist_ok=True)

    files = sorted(
        (f.name for f in folder.iterdir() if f.is_file() and store.is_media(f.name)),
        key=store.natural_key,
    )

    meta = {"active": "", "alt": ""}
    path = folder / SLOT_META
    if path.exists():
        try:
            meta.update(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass

    active = meta["active"] if meta["active"] in files else (files[0] if files else "")
    rel = f"assets/home/{spec['folder']}"

    return {
        **spec,
        "active": active,
        "url": f"{rel}/{active}" if active else spec["fallback"],
        "using_fallback": not active,
        "images": [{"name": n, "url": f"{rel}/{n}"} for n in files],
        "folder_abs": str(folder),
    }


def write_slot(key: str, active: str) -> None:
    folder = slot_dir(key)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / SLOT_META).write_text(
        json.dumps({"active": active}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def slots() -> list[dict]:
    return [read_slot(spec) for spec in SLOTS]


def slot_url(key: str) -> str:
    return read_slot(next(s for s in SLOTS if s["key"] == key))["url"]


# ----------------------------------------------------------------------
# Sinh HTML
# ----------------------------------------------------------------------


def esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def multiline(text: str) -> str:
    """Xuống dòng trong ô nhập -> <br /> trên web."""
    return "<br />".join(esc(line) for line in (text or "").split("\n"))


# Mã màu vàng nằm cứng bên trong 9 file icon kỹ năng (.svg). Khác một chút
# so với màu nhấn của web (#ffda24) vì bộ icon vẽ riêng.
ICON_YELLOW = "#FFDC31"

ICON_DIR = REPO / "assets" / "icons"


def render_icon(name: str) -> str:
    """
    Nhúng thẳng nội dung file .svg vào trang thay vì dùng thẻ <img>.

    Lý do: ảnh nạp qua <img> là một tài liệu riêng, CSS của trang không với
    vào trong được — nên icon sẽ mãi vàng dù người dùng đổi màu chủ đạo.
    Nhúng thẳng vào thì đổi được: mã vàng cứng trong file được thay bằng
    currentColor, và CSS chỉ việc đặt màu chữ cho nó.

    File không phải .svg (hoặc đọc không được) thì quay về dùng <img> như cũ.
    """
    duong = ICON_DIR / name
    if duong.suffix.lower() != ".svg" or not duong.is_file():
        return f'<img src="assets/icons/{esc(name)}" alt="" />'

    try:
        svg = duong.read_text(encoding="utf-8")
    except OSError:
        return f'<img src="assets/icons/{esc(name)}" alt="" />'

    svg = svg[svg.index("<svg") :] if "<svg" in svg else svg
    svg = svg.replace(ICON_YELLOW, "currentColor").replace(ICON_YELLOW.lower(), "currentColor")

    # id bên trong <defs> (clip-path, pattern...) là chung cho cả trang khi
    # nhúng thẳng. Chín icon dùng trùng id là đè nhau, hình vỡ hết — nên
    # thêm tiền tố riêng cho từng icon.
    rieng = "ic-" + duong.stem
    for cu in sorted(set(re.findall(r'id="([^"]+)"', svg)), key=len, reverse=True):
        svg = svg.replace(f'id="{cu}"', f'id="{rieng}-{cu}"')
        svg = svg.replace(f"url(#{cu})", f"url(#{rieng}-{cu})")

    svg = svg.replace("<svg ", '<svg class="skill-icon" aria-hidden="true" ', 1)
    return " ".join(svg.split())


def render_hero(cfg: dict) -> list[str]:
    h = cfg["hero"]
    return [
        '      <section class="hero container">',
        f"        <h1>{esc(h['title'])}</h1>",
        f"        <p>{esc(h['subtitle_left'])} <span>|</span> {esc(h['subtitle_right'])}</p>",
        f'        <a class="btn" href="{esc(h["button_href"])}">',
        f"          <strong>{esc(h['button_text'])}</strong>",
        "          <span>→</span>",
        "        </a>",
        "      </section>",
    ]


def render_about(cfg: dict) -> list[str]:
    a = cfg["about"]
    external = a["button_href"].startswith("http")
    link_attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
    return [
        '      <section class="about container" id="about">',
        '        <div class="about-copy">',
        f"          <h2>{multiline(a['heading'])}</h2>",
        f"          <p>{multiline(a['text'])}</p>",
        f'          <a class="btn small" href="{esc(a["button_href"])}"{link_attrs}>',
        f"            <strong>{esc(a['button_text'])}</strong>",
        "          </a>",
        "        </div>",
        '        <div class="portrait-wrap">',
        f'          <img src="{esc(webimg.web_url(slot_url("portrait"), "full"))}"'
        f' alt="{esc(a["image_alt"])}" class="portrait-img" loading="lazy" decoding="async" />',
        '          <i class="deco deco-a"></i>',
        '          <i class="deco deco-b"></i>',
        "        </div>",
        "      </section>",
    ]


def render_skills(cfg: dict) -> list[str]:
    s = cfg["skills"]
    out = [
        '      <section class="skills container">',
        f"        <h2>{multiline(s['heading'])}</h2>",
        '        <div class="skill-list">',
    ]
    for item in s["items"]:
        out += [
            '          <span class="skill-item">',
            f"            {render_icon(item['icon'])}",
            f"            {esc(item['text'])}",
            "          </span>",
        ]
    out += ["        </div>", "      </section>"]
    return out


def render_clients(cfg: dict) -> list[str]:
    c = cfg["clients"]
    return [
        '      <section class="clients container" id="portfolio">',
        '        <div class="clients-intro">',
        f"          <h2>{multiline(c['heading'])}</h2>",
        f"          <p>{multiline(c['text'])}</p>",
        "        </div>",
        '        <div class="portfolio-board">',
        f'          <img src="{esc(webimg.web_url(slot_url("clients"), "full"))}"'
        f' alt="{esc(c["image_alt"])}" class="clients-img" loading="lazy" decoding="async" />',
        '          <i class="deco board-left"></i>',
        '          <i class="deco board-right"></i>',
        "        </div>",
        "      </section>",
    ]


RENDERERS = {
    "hero": render_hero,
    "about": render_about,
    "skills": render_skills,
    "clients": render_clients,
}


def render(cfg: dict | None = None) -> str:
    cfg = cfg or load()
    out = [f"      {START}"]
    for name in cfg["sections"]:
        if name in cfg["hidden"]:
            continue
        out += RENDERERS[name](cfg)
        out.append("")
    out.append(f"      {END}")
    return "\n".join(out)


def build() -> dict:
    cfg = load()
    html = PAGE.read_text(encoding="utf-8")
    block = render(cfg)

    if START in html and END in html:
        i = html.index(START)
        j = html.index(END) + len(END)
        html = html[:i] + block.lstrip() + html[j:]
    else:
        # Lần đầu: thay ruột <main id="top"> ... </main>
        anchor = '<main id="top">'
        i = html.index(anchor) + len(anchor)
        j = html.index("</main>", i)
        html = html[:i] + "\n" + block + "\n    " + html[j:]

    PAGE.write_text(html, encoding="utf-8")

    shown = [s for s in cfg["sections"] if s not in cfg["hidden"]]
    return {"sections": len(shown), "skills": len(cfg["skills"]["items"])}


if __name__ == "__main__":
    print(build())
