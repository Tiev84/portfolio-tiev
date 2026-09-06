# -*- coding: utf-8 -*-
"""
webimg.py — tạo bản ảnh nhẹ cho web.

Vấn đề: thư mục project chứa file thiết kế gốc, có tấm 4500x3519 nặng 30 MB.
Web đang gửi thẳng những file đó cho người xem, trong khi khung hiển thị chỉ
rộng 420px. Trên điện thoại là chờ mòn mỏi.

Cách làm: giữ nguyên file gốc (đó là bản gốc của bạn, đừng đụng vào), nhưng
sinh thêm một bản nhẹ trong assets/_web/ rồi cho trang web dùng bản đó.

Bản nhẹ được sinh lại khi file gốc thay đổi, và tự xoá khi file gốc bị xoá.
Thiếu Pillow thì mọi thứ vẫn chạy — chỉ là web quay về dùng ảnh gốc như cũ.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WEB_DIR = REPO / "assets" / "_web"
INDEX = WEB_DIR / "_index.json"

# Bề ngang tối đa của từng cỡ (px). Nhân đôi so với kích thước hiển thị thật
# để màn hình Retina vẫn nét.
SIZES = {
    "cover": 900,  # thumbnail trong lưới portfolio (hiển thị ~420px)
    "full": 1600,  # ảnh trong trang chi tiết và trang chủ (hiển thị ~850px)
}

QUALITY = 82

# WebP: nhẹ hơn JPEG chừng 30% ở cùng chất lượng, giữ được nền trong suốt,
# và mọi trình duyệt từ 2020 tới nay đều đọc được.
EXT = ".webp"

try:
    from PIL import Image, ImageOps

    HAS_PIL = True
except Exception:
    HAS_PIL = False


def _load_index() -> dict:
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_index(data: dict) -> None:
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )


_INDEX: dict = _load_index()
_DIRTY = False

# Mọi ảnh nhẹ đã được trả ra trong lần build này. Dùng để biết ảnh nào còn
# được dùng, ảnh nào là rác của project đã xoá.
_USED: set[str] = set()


def begin() -> None:
    """Gọi ở đầu mỗi lần build, trước khi sinh trang."""
    _USED.clear()


def used() -> set[str]:
    return set(_USED)


def out_path(rel: str, size: str) -> Path:
    """assets/project/GALA/a.png  ->  assets/_web/cover/project/GALA/a.png.webp"""
    return WEB_DIR / size / (rel.split("assets/", 1)[-1] + EXT)


def web_url(rel: str, size: str = "full") -> str:
    """
    Đường dẫn ảnh nhẹ cho trang web. Chưa tạo được thì trả lại ảnh gốc,
    để trang không bao giờ bị vỡ ảnh.
    """
    global _DIRTY

    src = REPO / rel
    if not HAS_PIL or size not in SIZES or not src.is_file():
        return rel

    try:
        stat = src.stat()
    except OSError:
        return rel

    dau = f"{stat.st_mtime_ns}:{stat.st_size}:{SIZES[size]}:{QUALITY}"
    khoa = f"{size}|{rel}"
    dich = out_path(rel, size)

    ra = str(dich.relative_to(REPO)).replace("\\", "/")

    if _INDEX.get(khoa) == dau and dich.is_file():
        _USED.add(ra)
        return ra

    if not _convert(src, dich, SIZES[size]):
        return rel

    _INDEX[khoa] = dau
    _DIRTY = True
    _USED.add(ra)
    return ra


def _convert(src: Path, dich: Path, rong: int) -> bool:
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)  # ảnh chụp dọc khỏi bị nằm ngang

            # Ảnh đã nhỏ hơn khổ đích thì đừng phóng to, chỉ nén lại
            if im.width > rong:
                cao = max(1, round(im.height * rong / im.width))
                im = im.resize((rong, cao), Image.LANCZOS)

            co_trong_suot = im.mode in ("RGBA", "LA") or (
                im.mode == "P" and "transparency" in im.info
            )
            im = im.convert("RGBA" if co_trong_suot else "RGB")

            dich.parent.mkdir(parents=True, exist_ok=True)
            im.save(dich, "WEBP", quality=QUALITY, method=6)
        return True
    except Exception:
        # Ảnh hỏng, định dạng lạ, hết chỗ trống... web vẫn phải chạy được
        return False


def flush() -> None:
    """Ghi lại sổ theo dõi sau khi build xong."""
    global _DIRTY
    if _DIRTY:
        _save_index(_INDEX)
        _DIRTY = False


def prune(dang_dung: set[str]) -> int:
    """
    Xoá bản nhẹ của những ảnh đã bị gỡ khỏi web.

    dang_dung = tập đường dẫn ảnh nhẹ mà trang web đang thật sự trỏ tới.
    """
    global _DIRTY
    if not WEB_DIR.is_dir():
        return 0

    xoa = 0
    for f in WEB_DIR.rglob("*" + EXT):
        rel = str(f.relative_to(REPO)).replace("\\", "/")
        if rel not in dang_dung:
            try:
                f.unlink()
                xoa += 1
            except OSError:
                pass

    if xoa:
        con = {k: v for k, v in _INDEX.items() if out_path(k.split("|", 1)[1], k.split("|", 1)[0]).is_file()}
        _INDEX.clear()
        _INDEX.update(con)
        _DIRTY = True

    # dọn thư mục rỗng còn sót
    for d in sorted(WEB_DIR.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            try:
                d.rmdir()
            except OSError:
                pass
    return xoa


def stats() -> dict:
    goc = nhe = 0
    for khoa in _INDEX:
        size, rel = khoa.split("|", 1)
        s, d = REPO / rel, out_path(rel, size)
        if s.is_file() and d.is_file():
            goc += s.stat().st_size
            nhe += d.stat().st_size
    return {"count": len(_INDEX), "source_bytes": goc, "web_bytes": nhe}
