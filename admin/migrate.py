# -*- coding: utf-8 -*-
"""
migrate.py — chạy MỘT LẦN để gom ảnh đang nằm rải rác trong
assets/project/ vào từng thư mục riêng của mỗi project.

    python admin/migrate.py            # chỉ xem trước, không đụng gì
    python admin/migrate.py --apply    # thực sự di chuyển file
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import store  # noqa: E402

PROJECT_DIR = store.PROJECT_DIR

# order, id, tên thư mục, wide, category, title, description, [ảnh theo thứ tự], [ảnh giữ lại nhưng ẩn]
PLAN = [
    dict(
        order=1,
        id="event-droppii",
        folder="GALA",
        wide=True,
        category="SOCIAL MEDIA | EVENT | POSM | UI - UX DESIGN",
        title="Event Đại hội năm 2026 Droppii",
        description=(
            "Trong khuôn khổ Đại hội năm Droppii 2026, Tiến trực tiếp đảm nhiệm việc thực thi "
            "toàn bộ giải pháp hình ảnh cho sự kiện, từ các thiết kế Social Post truyền thông "
            "trước, trong và sau chương trình, hệ thống POSM in ấn đồng bộ (standee, backdrop, "
            "photobooth, thẻ đeo...) cho đến các ấn phẩm in ấn cỡ lớn và hiệu ứng màn hình LED "
            "trình chiếu trên sân khấu. Sự tỉ mỉ và đồng bộ trong từng nét vẽ đã góp phần tạo nên "
            "một không gian sự kiện chỉn chu, chuyên nghiệp và đầy cảm xúc."
        ),
        images=[
            "thumb dhn.jpg", "video.mp4", "3.jpg", "4.jpg", "5.jpg", "6.png", "7.png",
            "8.png", "9.png", "10.png", "11.png", "12.png", "13.png", "14.jpg", "15.jpg",
            "16.png", "17.png", "18.jpg", "19.png", "20.jpg", "21.jpg", "22.jpg",
            "23.jpg", "24.jpg",
        ],
        hidden=["12h.png", "619556438_2633119150377312_1179977227882623657_n.jpg"],
    ),
    dict(
        order=2,
        id="digital-advertising-droppii",
        folder="DIGITAL ADVERTISING DROPPII",
        wide=True,
        category="SOCIAL MEDIA | UI - UX DESIGN",
        title="Digital advertising Droppii",
        description=(
            "Các thiết kế Digital Advertising được phát triển nhằm đảm bảo tính đồng nhất "
            "thương hiệu, khả năng truyền tải thông tin nhanh và hiệu quả trên các nền tảng số."
        ),
        images=[
            "thumb ads (1).png", "153 OPT2.png", "180.png", "ADS 5.png", "2.png", "5.png",
            "ADS 4.png", "ADS PT TEXT 2.png", "181.png", "ADS 6.png", "LP ADS.png",
            "Landingpage droppii mall sua.png", "LP AI (1).png",
        ],
        hidden=[],
    ),
    dict(
        order=3,
        id="expo-hang-moi-droppii",
        folder="EXPO HANG MOI DROPPII",
        wide=False,
        category="SOCIAL MEDIA | POSM",
        title="Expo hàng mới lên kệ Droppii",
        description=(
            "Hệ thống thiết kế truyền thông và POSM phục vụ hoạt động giới thiệu các sản phẩm "
            "mới trên nền tảng Droppii."
        ),
        images=[],
        hidden=[],
    ),
    dict(
        order=4,
        id="expo-health",
        folder="EXPO SUC KHOE DROPPII",
        wide=False,
        category="SOCIAL MEDIA | POSM",
        title="Expo sức khỏe Droppii",
        description="Meta meta meta",
        images=[
            "thumb expo (1).png", "DIEM HEN SUC KHOE TEASER 2.png", "bia km.png",
            "TRAI NGHIEM GI.png", "backdrop.png", "standee.png", "pic.png",
        ],
        hidden=["REMIND HN.png"],
    ),
    dict(
        order=5,
        id="sale-event",
        folder="SALE EVENT DROPPII",
        wide=False,
        category="SOCIAL MEDIA | UI - UX DESIGN",
        title="Sale event Droppii",
        description="Meta meta meta",
        images=[
            "thumb 283 (1).png", "teaser.png", "full rule 28 vuong.png",
            "full rule 28 vuong 2.png", "bia km (1).png", "LP.png",
        ],
        hidden=[],
    ),
    dict(
        order=6,
        id="sale-campaign-nhan-duyen",
        folder="SALE CAMPAIGN NHAN DUYEN",
        wide=True,
        category="SOCIAL MEDIA | POSM",
        title="Sale campaign Nhà hàng Chay Nhân Duyên",
        description="",
        images=[],
        hidden=[],
    ),
    dict(
        order=7,
        id="vu-lan-nhan-duyen",
        folder="VU LAN NHAN DUYEN",
        wide=True,
        category="SOCIAL MEDIA | POSM",
        title="Campaign Vu Lan Nhà hàng Chay Nhân Duyên",
        description="",
        images=[],
        hidden=[],
    ),
    dict(
        order=8,
        id="bingto-vlog",
        folder="ĐIỀN QUÂN NETWORK",
        wide=False,
        category="SOCIAL MEDIA",
        title="Bingto Vlog - Điền Quân Network",
        description="Meta meta meta",
        images=[
            "cbcbec8a-38d6-4b37-9fd6-b3ad05e4fda9.jpg",
            "bingto vlog poster.png",
        ],
        hidden=[],
    ),
    dict(
        order=9,
        id="king-jades-83",
        folder="KING JADES 8.3",
        wide=False,
        category="SOCIAL MEDIA",
        title="Campaign 8.3 King Jades",
        description="",
        images=[],
        hidden=[],
    ),
    dict(
        order=10,
        id="fnb-menu",
        folder="FNB MENU",
        wide=False,
        category="PRINTING",
        title="FnB Menu design",
        description="",
        images=[],
        hidden=[],
    ),
    dict(
        order=11,
        id="logofolio",
        folder="LOGOFOLIO",
        wide=True,
        category="BRANDING",
        title="Logofolio - Nhiều thương hiệu",
        description="",
        images=[],
        hidden=[],
    ),
    dict(
        order=12,
        id="ooh",
        folder="OOH - PANO - BACKDROP",
        wide=True,
        category="LARGE SCALE PRINTING",
        title="OOH - Pano - Backdrop ngoài trời",
        description="",
        images=[],
        hidden=[],
    ),
]


def main(apply: bool) -> None:
    loose = {f.name for f in PROJECT_DIR.iterdir() if f.is_file() and store.is_media(f.name)}
    moves: list[tuple[str, str]] = []
    missing: list[str] = []

    print(f"Repo: {store.REPO}\n")

    for spec in PLAN:
        folder = PROJECT_DIR / spec["folder"]
        exists = folder.is_dir()
        print(f"[{spec['order']:02d}] {spec['folder']}  ({'có sẵn' if exists else 'TẠO MỚI'})")

        for name in spec["images"] + spec["hidden"]:
            if exists and (folder / name).is_file():
                continue  # đã nằm đúng chỗ
            if name in loose:
                moves.append((name, spec["folder"]))
                print(f"       chuyển vào  ←  {name}")
            else:
                missing.append(f"{spec['folder']} / {name}")

    used = {name for name, _ in moves}
    leftovers = sorted(loose - used)

    print("\n" + "-" * 62)
    print(f"Sẽ tạo/giữ {len(PLAN)} thư mục project")
    print(f"Sẽ di chuyển {len(moves)} file")
    if missing:
        print(f"\nKhông tìm thấy {len(missing)} file (bỏ qua):")
        for item in missing:
            print(f"   - {item}")
    if leftovers:
        print(f"\nFile lẻ không thuộc project nào — GIỮ NGUYÊN tại assets/project/:")
        for item in leftovers:
            print(f"   - {item}")
    print("-" * 62)

    if not apply:
        print("\nĐây mới chỉ là xem trước. Chạy lại với --apply để thực hiện.")
        return

    for spec in PLAN:
        folder = PROJECT_DIR / spec["folder"]
        folder.mkdir(parents=True, exist_ok=True)

    for name, folder_name in moves:
        src = PROJECT_DIR / name
        dest = store.unique_path(PROJECT_DIR / folder_name, name)
        shutil.move(str(src), str(dest))

    for spec in PLAN:
        folder = PROJECT_DIR / spec["folder"]
        on_disk = {f.name for f in folder.iterdir() if f.is_file() and store.is_media(f.name)}
        images = [n for n in spec["images"] if n in on_disk]
        hidden = [n for n in spec["hidden"] if n in on_disk]
        store.write_meta(
            folder,
            {
                "id": spec["id"],
                "title": spec["title"],
                "category": spec["category"],
                "description": spec["description"],
                "wide": spec["wide"],
                "order": spec["order"],
                "cover": images[0] if images else "",
                "images": images,
                "hidden": hidden,
            },
        )
        print(f"  ✓ {spec['folder']}: {len(images)} ảnh")

    print("\nĐang tạo lại js/projects-data.js và portfolio.html…")
    result = store.build()
    print(f"  ✓ {result['projects']} project · {result['images']} ảnh")
    print("\nXong. Chạy `python admin/server.py` để mở app.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
