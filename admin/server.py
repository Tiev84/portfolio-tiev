# -*- coding: utf-8 -*-
"""
Portfolio Manager — app localhost quản lý ảnh cho portfolio-tiev.

Chạy:  python admin/server.py     (hoặc double-click start.bat ở gốc repo)
Mở:    http://localhost:4321

Máy chủ này chỉ nghe trên 127.0.0.1 nên không ai ngoài máy bạn vào được.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import home  # noqa: E402
import store  # noqa: E402
import theme  # noqa: E402

REPO = store.REPO
UI_DIR = Path(__file__).resolve().parent / "ui"
CACHE_DIR = Path(__file__).resolve().parent / "_cache"
PORT = int(os.environ.get("PORTFOLIO_ADMIN_PORT", "4321"))

MAX_UPLOAD = 200 * 1024 * 1024  # 200 MB / file

try:
    from PIL import Image, ImageOps

    HAS_PIL = True
except Exception:  # thiếu Pillow, hoặc Pillow cài hỏng/sai kiến trúc máy
    HAS_PIL = False  # app vẫn chạy, chỉ là ảnh xem trước nặng hơn


# ----------------------------------------------------------------------
# Git
# ----------------------------------------------------------------------


# Biến môi trường chặn git hỏi đăng nhập. Nếu máy lỡ có sẵn mấy biến này
# (do một công cụ khác đặt), git sẽ báo "Cannot prompt" thay vì hiện ô đăng
# nhập — nên app luôn dọn sạch chúng trước khi gọi git.
BLOCKS_LOGIN_PROMPT = ("GCM_INTERACTIVE", "GIT_ASKPASS", "SSH_ASKPASS")


def git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k not in BLOCKS_LOGIN_PROMPT}
    env["GIT_TERMINAL_PROMPT"] = "1"
    return env


def git(*args: str, timeout: int = 900) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=git_env(),
    )
    # Chỉ cắt khoảng trắng cuối: `git status --porcelain` dùng khoảng trắng
    # ĐẦU dòng làm mã trạng thái, cắt đi là mất ký tự đầu của tên file.
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).rstrip()


AUTH_HINTS = (
    "could not read username",
    "authentication failed",
    "terminal prompts disabled",
    "invalid username or password",
    "permission denied",
    "403",
)


def looks_like_auth_error(text: str) -> bool:
    low = text.lower()
    return any(hint in low for hint in AUTH_HINTS)


# Không nối được tới GitHub: rớt mạng, nhà mạng chặn, tường lửa, GitHub sập...
# Khác hẳn lỗi đăng nhập nên phải báo khác, kèm nút thử lại.
NETWORK_HINTS = (
    "could not connect to server",
    "failed to connect",
    "could not resolve host",
    "couldn't resolve host",
    "connection timed out",
    "operation timed out",
    "connection reset",
    "network is unreachable",
    "recv failure",
    "send failure",
    "ssl_error",
    "gnutls_handshake",
    "unable to access",
)


def looks_like_network_error(text: str) -> bool:
    low = text.lower()
    if looks_like_auth_error(text):
        return False
    return any(hint in low for hint in NETWORK_HINTS)


def unpushed_count() -> int:
    """Số commit đã lưu ở máy nhưng chưa đẩy lên GitHub."""
    code, out = git("rev-list", "--count", "@{u}..HEAD", timeout=30)
    out = out.strip()
    return int(out) if code == 0 and out.isdigit() else 0


def git_status() -> dict:
    code, out = git("status", "--porcelain")
    if code != 0:
        return {"ok": False, "error": out, "changes": [], "ahead": 0}
    changes = []
    for line in out.splitlines():
        if len(line) > 3:
            # 2 ký tự đầu là mã trạng thái, ký tự thứ 3 là dấu cách ngăn cách
            changes.append({"state": line[:2].strip() or "?", "path": line[3:].strip().strip('"')})
    _, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    branch = branch.strip()
    return {"ok": True, "branch": branch, "changes": changes, "ahead": unpushed_count()}


# ----------------------------------------------------------------------
# Thumbnail
# ----------------------------------------------------------------------


def thumbnail(rel_path: str, width: int) -> tuple[bytes, str] | None:
    src = (REPO / rel_path).resolve()
    if not str(src).startswith(str(REPO)) or not src.is_file():
        return None
    if store.is_video(src.name) or not HAS_PIL or src.suffix.lower() == ".svg":
        return None

    stat = src.stat()
    key = hashlib.sha1(
        f"{rel_path}|{stat.st_mtime_ns}|{stat.st_size}|{width}".encode()
    ).hexdigest()
    cached = CACHE_DIR / f"{key}.jpg"
    if cached.exists():
        return cached.read_bytes(), "image/jpeg"

    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", im.size, (27, 27, 27))
                im = im.convert("RGBA")
                background.paste(im, mask=im.split()[-1])
                im = background
            else:
                im = im.convert("RGB")
            im.thumbnail((width, width * 4), Image.LANCZOS)
            buffer = io.BytesIO()
            im.save(buffer, "JPEG", quality=82, optimize=True)
    except Exception:
        return None

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = buffer.getvalue()
    cached.write_bytes(data)
    return data, "image/jpeg"


# ----------------------------------------------------------------------
# HTTP handler
# ----------------------------------------------------------------------


class Handler(SimpleHTTPRequestHandler):
    server_version = "PortfolioManager/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO), **kwargs)

    # -- tiện ích -------------------------------------------------------

    def log_message(self, fmt, *args):  # bớt ồn ào, nhưng đừng nuốt lỗi
        # Cẩn thận: log_error() truyền vào HTTPStatus chứ không phải chuỗi,
        # nên phải dựng câu trước rồi mới xét — kiểm tra args[0] là ném
        # TypeError và làm chết luôn luồng xử lý request.
        try:
            line = fmt % args
        except (TypeError, ValueError):
            line = str(fmt)
        if "/api/" in line or "code 4" in line or "code 5" in line:
            sys.stderr.write("  %s\n" % line)

    def send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, data: bytes, content_type: str, cache: str = "no-store") -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def end_headers(self):
        # Preview phải luôn thấy file mới nhất.
        # Phải cắt phần ?query= trước khi xét đuôi file — nếu không thì
        # "/project-detail.html?project=abc" không khớp ".html" và trình
        # duyệt sẽ giữ bản cũ trong cache.
        path = self.path.split("?", 1)[0]
        if path.endswith((".html", ".js", ".css")) or path.endswith("/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # -- GET ------------------------------------------------------------

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/admin/")
            self.end_headers()
            return

        if path.startswith("/api/"):
            return self.handle_api_get(path, parse_qs(parsed.query))

        if path == "/admin" or path == "/admin/":
            return self.serve_ui("index.html")
        if path.startswith("/admin/"):
            return self.serve_ui(path[len("/admin/") :])

        return super().do_GET()

    def serve_ui(self, name: str) -> None:
        target = (UI_DIR / name).resolve()
        if not str(target).startswith(str(UI_DIR)) or not target.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND)
        types = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".svg": "image/svg+xml",
        }
        ctype = types.get(target.suffix, "application/octet-stream")
        cache = "no-store" if target.suffix in (".html", ".js", ".css") else "max-age=3600"
        self.send_bytes(target.read_bytes(), ctype, cache=cache)

    def handle_api_get(self, path: str, query: dict) -> None:
        if path == "/api/projects":
            return self.send_json(
                {
                    "ok": True,
                    "repo": str(REPO),
                    "projects": store.scan(),
                    "placeholder": store.PLACEHOLDER_COVER,
                }
            )

        if path == "/api/thumb":
            rel = (query.get("path") or [""])[0]
            width = int((query.get("w") or ["420"])[0])
            result = thumbnail(rel, max(80, min(width, 1600)))
            if result is None:
                # Không tạo được thumbnail (video / svg) -> trả file gốc
                self.path = "/" + rel
                return super().do_GET()
            data, ctype = result
            return self.send_bytes(data, ctype, cache="max-age=86400")

        if path == "/api/home":
            return self.send_json(
                {
                    "ok": True,
                    "home": home.load(),
                    "defaults": home.DEFAULTS,
                    "slots": home.slots(),
                    "labels": home.SECTION_LABELS,
                    "icons": sorted(
                        f.name for f in (REPO / "assets" / "icons").glob("*.svg")
                    ),
                }
            )

        if path == "/api/theme":
            return self.send_json(
                {
                    "ok": True,
                    "theme": theme.load(),
                    "defaults": theme.DEFAULTS,
                    "fields": [
                        {"token": tk, "label": lb, "group": gr, "hint": hi}
                        for tk, lb, gr, hi in theme.COLOR_FIELDS
                    ],
                }
            )

        if path == "/api/git/status":
            return self.send_json({"ok": True, **git_status()})

        return self.send_error(HTTPStatus.NOT_FOUND)

    # -- POST -----------------------------------------------------------

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        if not path.startswith("/api/"):
            return self.send_error(HTTPStatus.NOT_FOUND)
        try:
            handler = getattr(self, "api_" + path[5:].replace("/", "_").replace("-", "_"), None)
            if handler is None:
                return self.send_error(HTTPStatus.NOT_FOUND)
            handler()
        except Exception as exc:  # trả lỗi ra UI thay vì chết âm thầm
            self.send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 500)

    # ---- project ------------------------------------------------------

    def _folder(self, project_id: str) -> Path:
        folder = store.folder_of(project_id)
        if folder is None:
            raise ValueError(f"Không tìm thấy project “{project_id}”")
        return folder

    def api_project_create(self):
        """
        Tạo một hoặc nhiều project cùng lúc.

        Trang portfolio xếp theo nhịp lặp "2 thẻ lớn + 3 thẻ nhỏ", nên tạo
        trọn một khối 5 cái là bố cục không bị lệch nhịp.
        """
        data = self.read_json()

        items = data.get("items")
        if not items:
            items = [
                {
                    "name": data.get("name"),
                    "title": data.get("title"),
                    "category": data.get("category"),
                    "description": data.get("description"),
                }
            ]

        existing = store.scan()  # phải quét TRƯỚC khi tạo, để tính số thứ tự cuối
        next_order = max([p["order"] for p in existing], default=0) + 1

        created, errors = [], []
        for offset, item in enumerate(items):
            name = store.safe_name((item.get("name") or "").strip())
            if not name:
                errors.append("Có dòng chưa nhập tên thư mục")
                continue

            folder = store.PROJECT_DIR / name
            if folder.exists():
                errors.append(f"“{name}” đã tồn tại")
                continue

            folder.mkdir(parents=True)
            meta = dict(store.DEFAULT_META)
            meta.update(
                {
                    "id": item.get("id") or store.slugify(name),
                    "title": (item.get("title") or name).strip(),
                    "category": (item.get("category") or "").strip(),
                    "description": (item.get("description") or "").strip(),
                    "wide": bool(item.get("wide")),
                    "order": next_order + offset,
                }
            )
            store.write_meta(folder, meta)
            created.append({"id": meta["id"], "folder": name})

        if not created:
            return self.send_json({"ok": False, "error": " · ".join(errors) or "Không tạo được"}, 400)

        self.send_json({"ok": True, "created": created, "errors": errors})

    def api_project_save(self):
        data = self.read_json()
        folder = self._folder(data["id"])
        meta = store.read_meta(folder)
        for key in ("title", "category", "description"):
            if key in data:
                meta[key] = (data[key] or "").strip()
        if "wide" in data:
            meta["wide"] = bool(data["wide"])
        store.write_meta(folder, meta)
        self.send_json({"ok": True})

    def api_project_delete(self):
        data = self.read_json()
        folder = self._folder(data["id"])
        dest = store.to_trash(folder)
        self.send_json({"ok": True, "trash": str(dest)})

    def api_project_rename_folder(self):
        data = self.read_json()
        folder = self._folder(data["id"])
        new_name = store.safe_name((data.get("folder") or "").strip())
        if not new_name:
            return self.send_json({"ok": False, "error": "Tên thư mục trống"}, 400)
        target = store.PROJECT_DIR / new_name
        if target.exists() and target != folder:
            return self.send_json({"ok": False, "error": "Đã có thư mục trùng tên"}, 400)
        folder.rename(target)
        self.send_json({"ok": True, "folder": new_name})

    def api_projects_reorder(self):
        ids = self.read_json().get("ids") or []
        for index, project_id in enumerate(ids, start=1):
            folder = store.folder_of(project_id)
            if folder is None:
                continue
            meta = store.read_meta(folder)
            meta["order"] = index
            store.write_meta(folder, meta)
        self.send_json({"ok": True})

    # ---- ảnh ----------------------------------------------------------

    def api_images_order(self):
        data = self.read_json()
        folder = self._folder(data["id"])
        meta = store.read_meta(folder)
        on_disk = {f.name for f in folder.iterdir() if f.is_file() and store.is_media(f.name)}
        meta["images"] = [n for n in data.get("images", []) if n in on_disk]
        meta["hidden"] = [
            n for n in data.get("hidden", []) if n in on_disk and n not in meta["images"]
        ]
        if meta["cover"] not in meta["images"]:
            meta["cover"] = meta["images"][0] if meta["images"] else ""
        store.write_meta(folder, meta)
        self.send_json({"ok": True})

    def api_images_cover(self):
        data = self.read_json()
        folder = self._folder(data["id"])
        meta = store.read_meta(folder)
        name = store.safe_name(data.get("name") or "")
        if name not in meta["images"]:
            return self.send_json({"ok": False, "error": "Ảnh không nằm trong project"}, 400)
        meta["cover"] = name
        store.write_meta(folder, meta)
        self.send_json({"ok": True})

    def api_images_delete(self):
        data = self.read_json()
        folder = self._folder(data["id"])
        name = store.safe_name(data.get("name") or "")
        target = folder / name
        if not target.is_file():
            return self.send_json({"ok": False, "error": "Không tìm thấy file"}, 404)
        dest = store.to_trash(target)

        meta = store.read_meta(folder)
        meta["images"] = [n for n in meta["images"] if n != name]
        meta["hidden"] = [n for n in meta["hidden"] if n != name]
        if meta["cover"] == name:
            meta["cover"] = meta["images"][0] if meta["images"] else ""
        store.write_meta(folder, meta)
        self.send_json({"ok": True, "trash": str(dest)})

    def api_images_upload(self):
        project_id = base64.b64decode(self.headers["X-Project-Id"]).decode("utf-8")
        filename = base64.b64decode(self.headers["X-Filename"]).decode("utf-8")
        folder = self._folder(project_id)

        name = store.safe_name(filename)
        if not store.is_media(name):
            return self.send_json({"ok": False, "error": f"“{name}” không phải ảnh/video"}, 400)

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_UPLOAD:
            return self.send_json({"ok": False, "error": "File rỗng hoặc quá lớn"}, 400)

        target = store.unique_path(folder, name)
        with open(target, "wb") as fh:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                fh.write(chunk)
                remaining -= len(chunk)

        meta = store.read_meta(folder)
        meta["images"].append(target.name)
        if not meta["cover"]:
            meta["cover"] = target.name
        store.write_meta(folder, meta)
        self.send_json({"ok": True, "name": target.name})

    # ---- build & git --------------------------------------------------

    def api_build(self):
        self.send_json({"ok": True, **store.build()})

    def api_git_publish(self):
        data = self.read_json()
        message = (data.get("message") or "").strip() or "Cập nhật portfolio"

        result = store.build()

        code, out = git("add", "-A")
        if code != 0:
            return self.send_json({"ok": False, "step": "add", "error": out}, 500)

        # Có thay đổi mới thì lưu lại. Không có cũng không sao — có thể lần
        # trước đã lưu rồi mà push hỏng, giờ chỉ cần push tiếp.
        commit_out = ""
        _, dirty = git("status", "--porcelain")
        if dirty.strip():
            code, commit_out = git("commit", "-m", message)
            if code != 0:
                return self.send_json({"ok": False, "step": "commit", "error": commit_out}, 500)

        ahead = unpushed_count()
        if ahead == 0:
            return self.send_json(
                {"ok": True, "nothing": True, "message": "Không có gì thay đổi để đăng.", **result}
            )

        code, push_out = git("push")
        if code != 0:
            print("\n--- git push thất bại ---\n" + push_out + "\n-------------------------\n")
            return self.send_json(
                {
                    "ok": False,
                    "step": "push",
                    "error": push_out,
                    "committed": True,
                    "ahead": ahead,
                    "auth": looks_like_auth_error(push_out),
                    "network": looks_like_network_error(push_out),
                },
                500,
            )

        self.send_json({"ok": True, "log": f"{commit_out}\n\n{push_out}".strip(), **result})

    def api_git_terminal(self):
        """
        Mở một cửa sổ dòng lệnh thật rồi chạy `git push` trong đó.

        Cần thiết vì lần đầu push, GitHub phải hỏi đăng nhập — mà app chạy nền
        thì không hiện được ô đăng nhập đó.
        """
        env = git_env()

        if sys.platform == "win32":
            subprocess.Popen(
                ["cmd", "/c", "start", "", "cmd", "/k", "git push & echo. & pause"],
                cwd=str(REPO),
                env=env,
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
            )
        elif sys.platform == "darwin":
            script = (
                f'tell application "Terminal" to do script '
                f'"cd {json.dumps(str(REPO))} && git push"\n'
                'tell application "Terminal" to activate'
            )
            subprocess.Popen(["osascript", "-e", script], env=env)
        else:
            return self.send_json({"ok": False, "error": "Hệ điều hành chưa hỗ trợ"}, 400)

        self.send_json({"ok": True})

    # ---- tiện ích hệ thống --------------------------------------------

    def api_home_save(self):
        cfg = home.save(self.read_json().get("home") or {})
        home.build()
        self.send_json({"ok": True, "home": cfg})

    def api_home_reset(self):
        cfg = home.save(home.DEFAULTS)
        home.build()
        self.send_json({"ok": True, "home": cfg})

    def api_home_slot_active(self):
        data = self.read_json()
        home.write_slot(data["key"], store.safe_name(data.get("name") or ""))
        home.build()
        self.send_json({"ok": True, "slots": home.slots()})

    def api_home_slot_upload(self):
        key = base64.b64decode(self.headers["X-Slot"]).decode("utf-8")
        filename = base64.b64decode(self.headers["X-Filename"]).decode("utf-8")
        folder = home.slot_dir(key)
        folder.mkdir(parents=True, exist_ok=True)

        name = store.safe_name(filename)
        if not store.is_media(name):
            return self.send_json({"ok": False, "error": f"“{name}” không phải ảnh"}, 400)

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_UPLOAD:
            return self.send_json({"ok": False, "error": "File rỗng hoặc quá lớn"}, 400)

        target = store.unique_path(folder, name)
        with open(target, "wb") as fh:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                fh.write(chunk)
                remaining -= len(chunk)

        # Ảnh mới tải lên thì dùng luôn — đó là điều người ta mong đợi
        home.write_slot(key, target.name)
        home.build()
        self.send_json({"ok": True, "name": target.name, "slots": home.slots()})

    def api_home_slot_delete(self):
        data = self.read_json()
        folder = home.slot_dir(data["key"])
        target = folder / store.safe_name(data.get("name") or "")
        if not target.is_file():
            return self.send_json({"ok": False, "error": "Không tìm thấy file"}, 404)
        store.to_trash(target)
        remain = home.read_slot(next(s for s in home.SLOTS if s["key"] == data["key"]))
        home.write_slot(data["key"], remain["active"])
        home.build()
        self.send_json({"ok": True, "slots": home.slots()})

    def api_home_open_folder(self):
        target = home.slot_dir(self.read_json()["key"])
        target.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(target))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        self.send_json({"ok": True})

    def api_theme_save(self):
        cfg = theme.save(self.read_json().get("theme") or {})
        theme.build()
        store.build()  # bố cục 2 lớn + 3 nhỏ có thể vừa bật/tắt
        self.send_json({"ok": True, "theme": cfg})

    def api_theme_reset(self):
        cfg = theme.save(theme.DEFAULTS)
        theme.build()
        store.build()
        self.send_json({"ok": True, "theme": cfg})

    def api_quit(self):
        self.send_json({"ok": True})
        # shutdown() phải gọi từ thread khác, không thì tự khoá chính mình
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def api_open_folder(self):
        data = self.read_json()
        target = self._folder(data["id"]) if data.get("id") else store.PROJECT_DIR
        if sys.platform == "win32":
            os.startfile(str(target))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        self.send_json({"ok": True, "path": str(target)})


# ----------------------------------------------------------------------


def already_running() -> bool:
    """Bấm icon hai lần thì đừng khởi động lần hai — chỉ mở lại trình duyệt."""
    import socket

    with socket.socket() as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", PORT)) == 0


def use_utf8_output() -> None:
    """
    Console Windows mặc định là cp1252, ghi log ra file cũng vậy — in tiếng Việt
    là ném UnicodeEncodeError và app chết ngay lúc khởi động. Ép UTF-8 tại đây
    thay vì trông chờ biến môi trường bên ngoài.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            # line_buffering: khi ghi ra file log (macOS) thì lỗi hiện ra ngay,
            # không bị kẹt trong bộ đệm lúc app chết.
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except (AttributeError, ValueError):
            pass


def main() -> None:
    use_utf8_output()

    if not (REPO / "portfolio.html").exists():
        sys.exit(f"Không thấy portfolio.html trong {REPO} — đặt thư mục admin/ vào gốc repo.")

    url = f"http://localhost:{PORT}/admin/"

    if already_running():
        print(f"App đang chạy sẵn rồi — mở lại {url}")
        webbrowser.open(url)
        return

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)

    print("=" * 60)
    print("  PORTFOLIO MANAGER")
    print("=" * 60)
    print(f"  Repo : {REPO}")
    print(f"  Mở   : {url}")
    if not HAS_PIL:
        print("  (!)  Chưa có Pillow -> ảnh xem trước sẽ nặng.")
        print("       Cài bằng:  python -m pip install Pillow")
    print('\n  Tắt app: bấm nút "Tắt app" trong trình duyệt, hoặc đóng cửa sổ này.')
    print("=" * 60)

    # Trên macOS, app bundle tự mở trình duyệt (đáng tin hơn khi chạy nền),
    # nên nó đặt PORTFOLIO_NO_BROWSER=1 để tránh mở hai lần.
    if os.environ.get("PORTFOLIO_NO_BROWSER") != "1":
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã tắt.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
