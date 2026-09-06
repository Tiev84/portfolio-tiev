# -*- coding: utf-8 -*-
"""
chatbot.py — soạn kịch bản hội thoại cho chatbot tawk.to.

Vì sao chỉ soạn rồi chép tay, không tự đẩy thẳng lên tawk.to:

    tawk.to KHÔNG mở cửa cho việc đó. REST API của họ chỉ làm được những
    việc như tạo property, đọc lịch sử chat, thống kê, webhook, bài viết
    Knowledge Base — không có chỗ nào tạo/sửa kịch bản chatbot. JavaScript
    API thì càng không: nó chỉ mở/đóng widget và gắn thông tin khách, không
    chèn được tin nhắn bot hay nút trả lời nhanh.

    Kịch bản chỉ sửa được trong dashboard của tawk.to.

Nên app làm phần việc còn lại cho tử tế: soạn kịch bản ở một chỗ, kiểm tra
lỗi logic (nhánh cụt, nút trỏ vào hư không, quá 4 gợi ý), giữ trong repo để
hai máy đồng bộ, rồi xuất ra đúng khuôn từng ô của tawk.to để chép sang.

Mô hình bám theo tawk.to:
    một NÚT hội thoại  =  một Shortcut
    tên tắt            =  gõ /tên-tắt để gọi
    nội dung           =  câu bot trả lời
    tối đa 4 gợi ý     =  các nút bấm khách thấy trong khung chat
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "chatbot.json"

# Giới hạn của tawk.to: mỗi shortcut tối đa 4 gợi ý trả lời nhanh
MAX_REPLIES = 4

DEFAULTS = {
    "nodes": [
        {
            "key": "chao",
            "title": "Lời chào mở đầu",
            "message": (
                "Chào bạn! Mình là trợ lý của Tiến — Graphics Designer.\n"
                "Bạn đang quan tâm điều gì ạ?"
            ),
            "replies": [
                {"text": "Xem bảng giá", "to": "bang-gia"},
                {"text": "Quy trình làm việc", "to": "quy-trinh"},
                {"text": "Xem portfolio", "to": "portfolio"},
                {"text": "Chat trực tiếp với Tiến", "to": "gap-nguoi"},
            ],
        },
        {
            "key": "bang-gia",
            "title": "Bảng giá",
            "message": (
                "Tiến báo giá theo từng hạng mục, tuỳ khối lượng và độ phức tạp.\n"
                "Bạn cần hạng mục nào ạ?"
            ),
            "replies": [
                {"text": "Social Post", "to": "gia-social"},
                {"text": "Thiết kế in ấn / POSM", "to": "gia-posm"},
                {"text": "Landing page / UI-UX", "to": "gia-uiux"},
                {"text": "Nhận báo giá riêng", "to": "gap-nguoi"},
            ],
        },
        {
            "key": "gia-social",
            "title": "Giá — Social Post",
            "message": (
                "Social Post tính theo bộ hoặc theo tháng.\n"
                "Gửi Tiến brief và số lượng bài, Tiến báo giá chính xác trong ngày nhé."
            ),
            "replies": [
                {"text": "Gửi brief ngay", "to": "gap-nguoi"},
                {"text": "Xem hạng mục khác", "to": "bang-gia"},
            ],
        },
        {
            "key": "gia-posm",
            "title": "Giá — In ấn / POSM",
            "message": (
                "POSM và ấn phẩm khổ lớn (backdrop, standee, photobooth, sign...) "
                "tính theo đầu hạng mục.\nBạn cho Tiến biết sự kiện và danh sách "
                "hạng mục cần làm nhé."
            ),
            "replies": [
                {"text": "Gửi danh sách hạng mục", "to": "gap-nguoi"},
                {"text": "Xem hạng mục khác", "to": "bang-gia"},
            ],
        },
        {
            "key": "gia-uiux",
            "title": "Giá — Landing page / UI-UX",
            "message": (
                "Landing page tính theo số màn hình và mức độ tương tác.\n"
                "Bạn mô tả sơ dự án để Tiến ước lượng nhé."
            ),
            "replies": [
                {"text": "Mô tả dự án", "to": "gap-nguoi"},
                {"text": "Xem hạng mục khác", "to": "bang-gia"},
            ],
        },
        {
            "key": "quy-trinh",
            "title": "Quy trình làm việc",
            "message": (
                "Quy trình của Tiến gồm 4 bước:\n"
                "1. Nhận brief và thống nhất phạm vi\n"
                "2. Gửi hướng thiết kế để bạn duyệt\n"
                "3. Triển khai và chỉnh sửa theo góp ý\n"
                "4. Bàn giao file gốc\n\n"
                "Bạn muốn biết thêm gì không ạ?"
            ),
            "replies": [
                {"text": "Thời gian bao lâu?", "to": "thoi-gian"},
                {"text": "Xem bảng giá", "to": "bang-gia"},
                {"text": "Bắt đầu dự án", "to": "gap-nguoi"},
            ],
        },
        {
            "key": "thoi-gian",
            "title": "Thời gian thực hiện",
            "message": (
                "Tuỳ hạng mục: một bộ Social Post thường 2-3 ngày, "
                "bộ POSM cho sự kiện thường 5-7 ngày.\n"
                "Gấp hơn thì báo Tiến, sắp xếp được ạ."
            ),
            "replies": [
                {"text": "Trao đổi với Tiến", "to": "gap-nguoi"},
                {"text": "Xem quy trình", "to": "quy-trinh"},
            ],
        },
        {
            "key": "portfolio",
            "title": "Xem portfolio",
            "message": (
                "Bạn xem các dự án của Tiến tại mục Portfolio trên web nhé — "
                "có đủ Social Media, POSM, Landing page và ấn phẩm sự kiện."
            ),
            "replies": [
                {"text": "Xem bảng giá", "to": "bang-gia"},
                {"text": "Chat trực tiếp với Tiến", "to": "gap-nguoi"},
            ],
        },
        {
            "key": "gap-nguoi",
            "title": "Chuyển cho người thật",
            "message": (
                "Bạn để lại nội dung và cách liên hệ nhé, Tiến sẽ trả lời sớm nhất.\n"
                "Nếu Tiến đang online thì trả lời ngay tại đây luôn ạ."
            ),
            "replies": [],
        },
    ]
}


# ----------------------------------------------------------------------
# Đọc / ghi
# ----------------------------------------------------------------------


def load() -> dict:
    if CONFIG.exists():
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
            if isinstance(data.get("nodes"), list):
                return {"nodes": [_clean_node(n) for n in data["nodes"]]}
        except (json.JSONDecodeError, OSError):
            pass
    return json.loads(json.dumps(DEFAULTS))


def save(data: dict) -> dict:
    nodes = [_clean_node(n) for n in (data or {}).get("nodes", [])]

    # Tên tắt phải riêng biệt: tawk.to gọi shortcut bằng tên, trùng tên là
    # gõ /ten ra nhầm câu.
    seen: set[str] = set()
    for node in nodes:
        base = node["key"] or "cau-tra-loi"
        key, i = base, 2
        while key in seen:
            key = f"{base}-{i}"
            i += 1
        node["key"] = key
        seen.add(key)

    out = {"nodes": nodes}
    CONFIG.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out


def slug(text: str) -> str:
    """Tên tắt chỉ nên có chữ thường, số và gạch ngang — gõ /ten cho nhanh."""
    import store

    return store.slugify(text)[:40]


def _clean_node(node: dict) -> dict:
    node = node or {}
    replies = []
    for r in (node.get("replies") or [])[:MAX_REPLIES]:
        text = (r.get("text") or "").strip()
        if text:
            replies.append({"text": text, "to": (r.get("to") or "").strip()})
    return {
        "key": (node.get("key") or "").strip(),
        "title": (node.get("title") or "").strip(),
        "message": (node.get("message") or "").rstrip(),
        "replies": replies,
    }


# ----------------------------------------------------------------------
# Kiểm tra kịch bản
# ----------------------------------------------------------------------


def check(cfg: dict | None = None) -> list[dict]:
    """
    Soi kịch bản tìm lỗi logic trước khi chép sang tawk.to.

    Sửa trong dashboard tawk.to rất mất công, nên bắt lỗi ở đây rẻ hơn nhiều.
    """
    cfg = cfg or load()
    nodes = cfg["nodes"]
    keys = {n["key"] for n in nodes}
    loi = []

    if not nodes:
        return [{"muc": "", "loai": "trong", "y": "Kịch bản chưa có nút nào."}]

    for n in nodes:
        ten = n["title"] or n["key"]

        if not n["message"].strip():
            loi.append({"muc": n["key"], "loai": "thieu", "y": f"“{ten}” chưa có nội dung trả lời."})

        if len(n["replies"]) > MAX_REPLIES:
            loi.append(
                {
                    "muc": n["key"],
                    "loai": "qua-nhieu",
                    "y": f"“{ten}” có {len(n['replies'])} gợi ý — tawk.to chỉ nhận tối đa {MAX_REPLIES}.",
                }
            )

        for r in n["replies"]:
            if not r["to"]:
                loi.append(
                    {
                        "muc": n["key"],
                        "loai": "chua-noi",
                        "y": f"Nút “{r['text']}” trong “{ten}” chưa nối tới nút nào.",
                    }
                )
            elif r["to"] not in keys:
                loi.append(
                    {
                        "muc": n["key"],
                        "loai": "gay",
                        "y": f"Nút “{r['text']}” trong “{ten}” trỏ tới “{r['to']}” — không có nút đó.",
                    }
                )

    # Nút không ai dẫn tới thì khách không bao giờ gặp (trừ nút đầu tiên,
    # đó là lời chào nên đương nhiên không ai dẫn tới)
    duoc_dan = {r["to"] for n in nodes for r in n["replies"]}
    for n in nodes[1:]:
        if n["key"] not in duoc_dan:
            loi.append(
                {
                    "muc": n["key"],
                    "loai": "mo-coi",
                    "y": f"“{n['title'] or n['key']}” không có nút nào dẫn tới — khách sẽ không bao giờ thấy.",
                }
            )

    return loi


# ----------------------------------------------------------------------
# Xuất ra để chép sang tawk.to
# ----------------------------------------------------------------------


def export_text(cfg: dict | None = None) -> str:
    """Toàn bộ kịch bản dưới dạng văn bản, để lưu lại hoặc gửi cho người khác."""
    cfg = cfg or load()
    out = [
        "KỊCH BẢN CHATBOT — chép sang tawk.to",
        "=" * 52,
        "",
        "Cách chép: dashboard.tawk.to → Shortcuts → Add Shortcut.",
        "Mỗi mục dưới đây là MỘT shortcut.",
        "",
    ]
    for i, n in enumerate(cfg["nodes"], 1):
        out += [
            f"--- {i}. {n['title'] or n['key']} " + "-" * 20,
            f"Shortcut name : {n['key']}",
            "Message       :",
        ]
        out += [f"    {d}" for d in n["message"].splitlines()]
        if n["replies"]:
            out.append(f"Suggested messages ({len(n['replies'])}/{MAX_REPLIES}):")
            for r in n["replies"]:
                out.append(f"    - {r['text']}   → dẫn tới shortcut “{r['to']}”")
        else:
            out.append("Suggested messages: (không có — đây là nút kết thúc)")
        out.append("")
    return "\n".join(out)
