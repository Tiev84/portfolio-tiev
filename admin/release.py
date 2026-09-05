# -*- coding: utf-8 -*-
"""
release.py — đưa video lên GitHub Releases.

Vì sao phải làm vậy: file .mp4 trong repo đi qua Git LFS, mà GitHub Pages và
Vercel KHÔNG đọc được LFS — web chỉ nhận về cái "phiếu gửi" vài trăm byte.
Bỏ LFS ra thì lại vướng trần 100 MB của file thường.

GitHub Releases không dính cả hai giới hạn đó: mỗi file tới 2 GB, link tải
công khai, web nhúng thẳng vào thẻ <video> được.

Chỉ dùng thư viện có sẵn của Python, không cần cài thêm gì.
"""

from __future__ import annotations

import json
import mimetypes
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

API = "https://api.github.com"
UPLOADS = "https://uploads.github.com"

# Toàn bộ video của portfolio nằm chung một bản phát hành này
TAG = "video"
RELEASE_NAME = "Video cho portfolio"
RELEASE_BODY = (
    "Kho video của website portfolio.\n\n"
    "Được tạo và quản lý tự động bởi app Portfolio Manager — "
    "đừng xoá tay ở đây, hãy xoá trong app.\n\n"
    "Lý do phải để video ở đây: GitHub Pages và Vercel không đọc được "
    "Git LFS, còn file thường thì GitHub chặn ở 100 MB."
)

TIMEOUT = 60

# Trần của GitHub Releases cho mỗi file
MAX_ASSET = 2 * 1024 * 1024 * 1024


class ReleaseError(Exception):
    """Lỗi có câu chữ đọc được, để hiện thẳng lên giao diện."""


# ----------------------------------------------------------------------
# Thông tin kho và thẻ đăng nhập
# ----------------------------------------------------------------------


def repo_slug() -> tuple[str, str]:
    """Lấy (chủ sở hữu, tên kho) từ địa chỉ remote."""
    proc = subprocess.run(
        ["git", "-C", str(REPO), "remote", "get-url", "origin"],
        capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    url = (proc.stdout or "").strip()
    match = re.search(r"github\.com[:/]+([^/]+)/(.+?)(?:\.git)?$", url)
    if not match:
        raise ReleaseError(f"Không đọc được địa chỉ kho GitHub từ: {url or '(trống)'}")
    return match.group(1), match.group(2)


def token() -> str:
    """
    Mượn lại thẻ đăng nhập mà git đã lưu sẵn cho github.com.

    Không hỏi lại người dùng, không lưu ra đâu cả, và tuyệt đối không in ra
    log hay trả về giao diện.
    """
    proc = subprocess.run(
        ["git", "-C", str(REPO), "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    for line in (proc.stdout or "").splitlines():
        if line.startswith("password="):
            value = line[len("password="):].strip()
            if value:
                return value
    raise ReleaseError(
        "Chưa đăng nhập GitHub trên máy này.\n"
        'Bấm "Đăng lên web" một lần để đăng nhập, rồi quay lại thêm video.'
    )


def _headers(tok: str, extra: dict | None = None) -> dict:
    head = {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "portfolio-manager",
    }
    head.update(extra or {})
    return head


def _call(url: str, tok: str, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    for key, value in _headers(tok, {"Content-Type": "application/json"} if data else None).items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read()
    except urllib.error.HTTPError as err:
        raise ReleaseError(_doc_loi(err)) from err
    except urllib.error.URLError as err:
        raise ReleaseError(
            f"Không nối được tới GitHub: {err.reason}\n"
            "Kiểm tra mạng rồi thử lại."
        ) from err

    return json.loads(raw) if raw else {}


def _doc_loi(err: urllib.error.HTTPError) -> str:
    """Đổi lỗi HTTP khô khan thành câu người dùng hiểu được."""
    try:
        chi_tiet = json.loads(err.read()).get("message", "")
    except Exception:
        chi_tiet = ""

    if err.code in (401, 403):
        return (
            "GitHub từ chối thẻ đăng nhập.\n"
            "Thẻ có thể đã hết hạn, hoặc thiếu quyền `repo`.\n"
            f"({err.code} {chi_tiet})"
        )
    if err.code == 404:
        return f"GitHub không tìm thấy mục cần thao tác. ({err.code} {chi_tiet})"
    if err.code == 422:
        return f"GitHub từ chối dữ liệu gửi lên. ({err.code} {chi_tiet})"
    return f"GitHub báo lỗi {err.code}. {chi_tiet}"


# ----------------------------------------------------------------------
# Bản phát hành
# ----------------------------------------------------------------------


def ensure_release(tok: str) -> dict:
    """Lấy bản phát hành chứa video; chưa có thì tạo."""
    owner, name = repo_slug()
    base = f"{API}/repos/{owner}/{name}/releases"

    try:
        return _call(f"{base}/tags/{urllib.parse.quote(TAG)}", tok)
    except ReleaseError as err:
        if "không tìm thấy" not in str(err).lower():
            raise

    return _call(
        base, tok, "POST",
        {"tag_name": TAG, "name": RELEASE_NAME, "body": RELEASE_BODY, "draft": False},
    )


def list_assets(tok: str | None = None) -> list[dict]:
    """
    Mọi file đang nằm trên Releases của kho — kể cả video bạn tự tay đưa lên
    trước đây ở một bản phát hành khác, để còn gắn lại vào project.
    """
    tok = tok or token()
    owner, name = repo_slug()
    rels = _call(f"{API}/repos/{owner}/{name}/releases?per_page=100", tok)
    if not isinstance(rels, list):
        return []

    ra = []
    for rel in rels:
        for a in rel.get("assets", []):
            ra.append(
                {
                    "id": a["id"],
                    "name": a["name"],
                    "size": a["size"],
                    "url": a["browser_download_url"],
                    "tag": rel.get("tag_name", ""),
                    # Chỉ file trong bản phát hành do app quản lý mới cho xoá
                    # trong app; file bạn tự đưa lên thì app không đụng vào.
                    "managed": rel.get("tag_name") == TAG,
                }
            )
    ra.sort(key=lambda a: a["name"].lower())
    return ra


def ten_asset(name: str) -> str:
    """
    Đổi tên file cho khớp cách GitHub đặt tên.

    GitHub thay mọi ký tự ngoài [A-Za-z0-9._-] bằng dấu chấm. Tự làm trước
    thì tên mình gửi lên và tên GitHub lưu là một, nhờ vậy việc dò trùng tên
    mới đúng.
    """
    return re.sub(r"[^A-Za-z0-9._-]", ".", name)


def upload(path: Path, ten_hien: str | None = None) -> dict:
    """
    Đưa một file lên bản phát hành. Trả về link tải công khai.

    Trùng tên thì xoá bản cũ trước — GitHub không cho hai file cùng tên.
    """
    tok = token()
    rel = ensure_release(tok)
    ten = ten_asset(ten_hien or path.name)

    for cu in rel.get("assets", []):
        if cu["name"] == ten:
            delete_asset(cu["id"], tok)

    owner, name = repo_slug()
    url = (
        f"{UPLOADS}/repos/{owner}/{name}/releases/{rel['id']}/assets"
        f"?name={urllib.parse.quote(ten)}"
    )
    kieu = mimetypes.guess_type(ten)[0] or "application/octet-stream"
    size = path.stat().st_size

    with open(path, "rb") as fh:
        request = urllib.request.Request(url, data=fh, method="POST")
        for key, value in _headers(
            tok, {"Content-Type": kieu, "Content-Length": str(size)}
        ).items():
            request.add_header(key, value)
        try:
            # Video nặng nên cho hẳn 30 phút
            with urllib.request.urlopen(request, timeout=1800) as response:
                asset = json.loads(response.read())
        except urllib.error.HTTPError as err:
            raise ReleaseError(_doc_loi(err)) from err
        except urllib.error.URLError as err:
            raise ReleaseError(f"Đứt kết nối khi đang tải lên: {err.reason}") from err

    return {
        "id": asset["id"],
        "name": asset["name"],
        "size": asset["size"],
        "url": asset["browser_download_url"],
    }


def delete_asset(asset_id: int, tok: str | None = None) -> None:
    tok = tok or token()
    owner, name = repo_slug()
    _call(f"{API}/repos/{owner}/{name}/releases/assets/{asset_id}", tok, "DELETE")


def find_asset(url: str, tok: str | None = None) -> dict | None:
    for a in list_assets(tok):
        if a["url"] == url:
            return a
    return None


if __name__ == "__main__":
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    print("Kho:", "/".join(repo_slug()))
    for a in list_assets():
        print(f"  {a['name']:50} {a['size'] / 1024 / 1024:8.1f} MB")
