# -*- coding: utf-8 -*-
"""
store.py — Lớp dữ liệu của Portfolio Manager.

Nguyên tắc: MỖI THƯ MỤC TRONG assets/project/ LÀ MỘT PROJECT.
Mỗi thư mục chứa một file _project.json giữ thông tin (tiêu đề, mô tả,
thứ tự ảnh...). Ảnh mới bỏ vào thư mục sẽ tự động được nhận ra khi quét.
"""

from __future__ import annotations

import json
import re
import shutil
import time
import unicodedata
from pathlib import Path

import home
import theme

REPO = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO / "assets" / "project"
TRASH_DIR = REPO / "admin" / "_trash"
META_NAME = "_project.json"

PLACEHOLDER_COVER = "assets/images/client.jpg"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}
VIDEO_EXT = {".mp4", ".webm", ".mov", ".ogg"}
MEDIA_EXT = IMAGE_EXT | VIDEO_EXT

GRID_START = "<!-- PROJECTS:START — tự động tạo bởi admin app, đừng sửa tay -->"
GRID_END = "<!-- PROJECTS:END -->"


# ----------------------------------------------------------------------
# Tiện ích
# ----------------------------------------------------------------------

_VN_GROUPS = {
    "a": "àáạảãâầấậẩẫăằắặẳẵ",
    "e": "èéẹẻẽêềếệểễ",
    "i": "ìíịỉĩ",
    "o": "òóọỏõôồốộổỗơờớợởỡ",
    "u": "ùúụủũưừứựửữ",
    "y": "ỳýỵỷỹ",
    "d": "đ",
}

_VN_MAP: dict[int, str] = {}
for _base, _chars in _VN_GROUPS.items():
    for _ch in _chars:
        _VN_MAP[ord(_ch)] = _base
        _VN_MAP[ord(_ch.upper())] = _base.upper()


def slugify(text: str) -> str:
    """Biến tên thư mục tiếng Việt thành id an toàn cho URL."""
    text = (text or "").translate(_VN_MAP)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "project"


_NUM_RE = re.compile(r"(\d+)")


def natural_key(name: str):
    """Sắp xếp 2.png trước 10.png (thay vì 10 trước 2)."""
    return [int(p) if p.isdigit() else p.lower() for p in _NUM_RE.split(name)]


def is_media(name: str) -> bool:
    return Path(name).suffix.lower() in MEDIA_EXT


def is_video(name: str) -> bool:
    return Path(name).suffix.lower() in VIDEO_EXT


def safe_name(name: str) -> str:
    """Chặn ../ và ký tự cấm của Windows trong tên file người dùng gửi lên."""
    name = Path(name).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "file"


def unique_path(folder: Path, name: str) -> Path:
    """Nếu trùng tên thì thêm (1), (2)... thay vì ghi đè."""
    target = folder / name
    if not target.exists():
        return target
    stem, suffix = Path(name).stem, Path(name).suffix
    i = 1
    while True:
        candidate = folder / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def to_trash(path: Path) -> Path:
    """Không xoá vĩnh viễn — chuyển vào admin/_trash/ để còn lấy lại được."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest_dir = TRASH_DIR / stamp
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = unique_path(dest_dir, path.name)
    shutil.move(str(path), str(dest))
    return dest


# ----------------------------------------------------------------------
# Đọc / ghi metadata
# ----------------------------------------------------------------------

DEFAULT_META = {
    "id": "",
    "title": "",
    "category": "",
    "description": "",
    "wide": False,
    "order": 999,
    "cover": "",
    "images": [],
    "hidden": [],
}


def read_meta(folder: Path) -> dict:
    meta = dict(DEFAULT_META)
    path = folder / META_NAME
    if path.exists():
        try:
            meta.update(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    if not meta.get("id"):
        meta["id"] = slugify(folder.name)
    if not meta.get("title"):
        meta["title"] = folder.name
    return meta


def write_meta(folder: Path, meta: dict) -> None:
    clean = {k: meta.get(k, DEFAULT_META[k]) for k in DEFAULT_META}
    (folder / META_NAME).write_text(
        json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ----------------------------------------------------------------------
# Quét thư mục
# ----------------------------------------------------------------------


def folder_of(project_id: str) -> Path | None:
    for folder in PROJECT_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith(("_", ".")):
            continue
        if read_meta(folder)["id"] == project_id:
            return folder
    return None


def scan(persist: bool = True) -> list[dict]:
    """
    Đọc toàn bộ project từ đĩa.

    Ảnh mới xuất hiện trong thư mục (do bạn copy tay vào) sẽ được nối
    vào cuối danh sách; ảnh đã bị xoá khỏi đĩa sẽ tự rớt ra.
    """
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    projects: list[dict] = []

    for folder in sorted(PROJECT_DIR.iterdir(), key=lambda p: natural_key(p.name)):
        if not folder.is_dir() or folder.name.startswith(("_", ".")):
            continue

        meta = read_meta(folder)
        on_disk = {f.name for f in folder.iterdir() if f.is_file() and is_media(f.name)}

        images = [n for n in meta["images"] if n in on_disk]
        hidden = [n for n in meta["hidden"] if n in on_disk]

        known = set(images) | set(hidden)
        new_files = sorted(on_disk - known, key=natural_key)
        images.extend(new_files)

        cover = meta["cover"] if meta["cover"] in images else (images[0] if images else "")

        changed = (
            images != meta["images"]
            or hidden != meta["hidden"]
            or cover != meta["cover"]
            or not (folder / META_NAME).exists()
        )

        meta.update({"images": images, "hidden": hidden, "cover": cover})
        if persist and changed:
            write_meta(folder, meta)

        rel = f"assets/project/{folder.name}"
        projects.append(
            {
                **meta,
                "folder": folder.name,
                "folder_abs": str(folder),
                "new_count": len(new_files),
                "cover_url": f"{rel}/{cover}" if cover else PLACEHOLDER_COVER,
                "items": [
                    {
                        "name": n,
                        "url": f"{rel}/{n}",
                        "video": is_video(n),
                        "hidden": False,
                        "size": (folder / n).stat().st_size,
                    }
                    for n in images
                ]
                + [
                    {
                        "name": n,
                        "url": f"{rel}/{n}",
                        "video": is_video(n),
                        "hidden": True,
                        "size": (folder / n).stat().st_size,
                    }
                    for n in hidden
                ],
            }
        )

    projects.sort(key=lambda p: (p["order"], natural_key(p["folder"])))

    # Bố cục lặp "2 thẻ lớn + 3 thẻ nhỏ": kích thước thẻ suy ra từ vị trí,
    # không lấy theo ô tick thủ công — như vậy kéo thả đổi thứ tự xong là
    # nhịp bố cục vẫn khớp.
    cfg = theme.load()
    if cfg["grid"]["auto_pattern"]:
        for index, project in enumerate(projects):
            project["wide"] = theme.is_wide(index, cfg)
            project["auto_wide"] = True
    else:
        for project in projects:
            project["auto_wide"] = False

    return projects


# ----------------------------------------------------------------------
# Sinh code cho website
# ----------------------------------------------------------------------


def _js_string(value: str) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def render_projects_data(projects: list[dict]) -> str:
    lines = [
        "/* =========================================================",
        "   File này được TẠO TỰ ĐỘNG bởi admin app (admin/server.py).",
        "   Đừng sửa tay — mở app rồi bấm lưu, file sẽ được ghi lại.",
        "   ========================================================= */",
        "",
        "window.PROJECTS = {",
    ]
    for p in projects:
        rel = f"assets/project/{p['folder']}"
        lines.append(f"  {_js_string(p['id'])}: {{")
        lines.append(f"    category: {_js_string(p['category'])},")
        lines.append(f"    title: {_js_string(p['title'])},")
        lines.append(f"    description: {_js_string(p['description'])},")
        lines.append("    images: [")
        for name in p["images"]:
            lines.append(f"      {_js_string(f'{rel}/{name}')},")
        lines.append("    ],")
        lines.append("  },")
    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def render_grid(projects: list[dict]) -> str:
    out = [f"          {GRID_START}"]
    for index, p in enumerate(projects, start=1):
        wide = " project-wide" if p["wide"] else ""
        out.append(f"          <!-- PROJECT {index:02d} -->")
        out.append(f'          <article class="project-card{wide}">')
        out.append(
            f'            <a href="project-detail.html?project={p["id"]}" class="project-link">'
        )
        out.append('              <div class="project-image">')
        out.append(f'                <img src="{p["cover_url"]}" alt="{_attr(p["title"])}" />')
        out.append("              </div>")
        out.append('              <div class="project-info">')
        out.append(f'                <p class="project-category">{_attr(p["category"])}</p>')
        out.append(f"                <h2>{_attr(p['title'])}</h2>")
        out.append("              </div>")
        out.append("            </a>")
        out.append("          </article>")
        out.append("")
    out.append(f"          {GRID_END}")
    return "\n".join(out)


def _attr(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _matching_div_close(html: str, start: int) -> int:
    """Trả về vị trí thẻ </div> đóng đúng cấp cho một <div> đã mở."""
    depth = 1
    i = start
    while i < len(html):
        opened = html.find("<div", i)
        closed = html.find("</div", i)
        if closed == -1:
            break
        if opened != -1 and opened < closed:
            depth += 1
            i = opened + 4
            continue
        depth -= 1
        if depth == 0:
            return closed
        i = closed + 5
    raise ValueError("Không tìm thấy </div> đóng cho .project-grid trong portfolio.html")


def build() -> dict:
    """Ghi css/theme.css, js/projects-data.js và lưới project trong portfolio.html."""
    theme.build()
    home.build()
    projects = scan()

    data_file = REPO / "js" / "projects-data.js"
    data_file.write_text(render_projects_data(projects), encoding="utf-8")

    page = REPO / "portfolio.html"
    html = page.read_text(encoding="utf-8")
    grid = render_grid(projects)

    if GRID_START in html and GRID_END in html:
        start = html.index(GRID_START)
        end = html.index(GRID_END) + len(GRID_END)
        html = html[:start] + grid.lstrip() + html[end:]
    else:
        # Lần đầu: tìm <div class="project-grid"> ... </div> rồi thay ruột nó
        anchor = '<div class="project-grid">'
        start = html.index(anchor) + len(anchor)
        end = _matching_div_close(html, start)
        html = html[:start] + "\n" + grid + "\n        " + html[end:]

    page.write_text(html, encoding="utf-8")

    return {
        "projects": len(projects),
        "images": sum(len(p["images"]) for p in projects),
        "files": ["css/theme.css", "index.html", "js/projects-data.js", "portfolio.html"],
    }
