# Portfolio Manager

App localhost để thêm / sửa / xóa ảnh cho portfolio mà không phải mở code.

---

## Cài đặt

### Windows

1. Bấm đúp **`install-windows.bat`** ở thư mục gốc của repo.
2. Xong — icon **Portfolio Manager** xuất hiện trên Desktop.

Trình cài đặt sẽ tự kiểm tra Python, cài Pillow, dựng icon và tạo shortcut.
Nếu báo thiếu Python: tải ở <https://www.python.org/downloads/>, nhớ tick
**"Add Python to PATH"** rồi chạy lại.

### macOS

Mở **Terminal** (Cmd + Space, gõ `terminal`), dán nguyên dòng này rồi Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/tiev84/portfolio-tiev/main/install-mac.command -o ~/Downloads/install-mac.command && chmod +x ~/Downloads/install-mac.command && ~/Downloads/install-mac.command
```

Trình cài đặt sẽ tự làm hết: tải portfolio về `~/Documents/portfolio-tiev`,
cài thư viện, tạo icon và đặt app **Portfolio Manager** vào Launchpad + Desktop.

Nếu đã tải repo về máy Mac rồi thì chỉ cần bấm đúp `install-mac.command`
trong thư mục repo.

**Cần có sẵn:** `git` và `python3`. Nếu thiếu, mở Terminal chạy:

```bash
xcode-select --install
```

Muốn xem được file video `.mp4` trong project GALA thì cài thêm git-lfs
(qua [Homebrew](https://brew.sh)):

```bash
brew install git-lfs
```

> Đổi chỗ thư mục portfolio trên máy Mac thì chạy lại `install-mac.command`,
> vì app nhớ đường dẫn cũ.

---

## Chạy app

- **Windows:** bấm icon **Portfolio Manager** trên Desktop (hoặc `start.bat`).
- **macOS:** bấm icon **Portfolio Manager** trên Desktop hoặc trong Launchpad.

Cả hai đều mở một cửa sổ dòng lệnh — đó chính là "máy chủ" của app, cứ để đó.
Trình duyệt tự mở <http://localhost:4321/admin/>.

**Tắt app:** bấm nút **Tắt app** góc trên bên phải trong giao diện.
(Trên Windows cũng có thể đóng cửa sổ đen đang thu nhỏ ở thanh taskbar.)

### Nếu bấm icon mà không lên (macOS)

Icon chỉ làm một việc: mở `start-mac.command` bằng Terminal. Nên:

1. Bấm đúp thẳng `start-mac.command` trong thư mục portfolio. Lỗi (nếu có)
   hiện ngay trong cửa sổ Terminal.
2. Nếu cách 1 chạy được mà icon thì không → chạy lại `install-mac.command`.
3. Mở trình duyệt vào <http://localhost:4321/admin/> để kiểm tra app có
   đang chạy sẵn không.

Bấm icon hai lần cũng không sao — app biết mình đang chạy rồi và chỉ mở lại tab.

---

## Cách hoạt động

**Mỗi thư mục trong `assets/project/` là một project.**

```
assets/project/
  ĐIỀN QUÂN NETWORK/
    _project.json          <- tên, mô tả, thứ tự ảnh (app tự ghi)
    bingto vlog poster.png
    cbcbec8a-....jpg
  EXPO SUC KHOE DROPPII/
    ...
```

- Bỏ ảnh mới vào thư mục bằng Explorer / Finder → bấm **Quét lại thư mục**
  trong app, ảnh tự động được thêm vào cuối danh sách.
- Xóa ảnh khỏi thư mục → ảnh tự rớt khỏi web ở lần quét sau.
- Không sửa tay `_project.json` — app sẽ ghi đè.

> **Muốn thêm project thì bấm "+ Project mới", đừng chép thư mục trong
> Explorer.** Chép thư mục sẽ chép luôn `_project.json` bên trong, hai thư mục
> mang cùng một mã định danh. App vẫn tự phát hiện và cấp mã mới cho bản sao,
> nhưng địa chỉ web của nó sẽ đổi.

Từ dữ liệu đó, app tạo lại bốn chỗ trên web:

| File | Nội dung |
|---|---|
| `css/theme.css` | màu sắc, phông, kích thước — dùng chung cho **cả 3 trang** |
| `index.html` | nội dung trang chủ, phần giữa `HOME:START` và `HOME:END` |
| `js/projects-data.js` | toàn bộ dữ liệu project |
| `portfolio.html` | lưới project, phần giữa `PROJECTS:START` và `PROJECTS:END` |

Cả bốn đều **tạo tự động, đừng sửa tay**. Phần còn lại của các file .html
(header, footer, script…) không bị đụng tới.

---

## Trang chủ

Tab **Trang chủ** sửa được toàn bộ chữ và 2 tấm ảnh của `index.html`.

**Hai khung ảnh** tổ chức theo thư mục y như project:

```
assets/home/
  chan-dung/       <- ảnh phần Giới thiệu
    _slot.json     <- ảnh nào đang dùng (app tự ghi)
    avt.jpg
  khach-hang/      <- ảnh phần Doanh nghiệp & khách hàng
    client.jpg
```

Bỏ nhiều ảnh vào một thư mục rồi **bấm vào ảnh nào là web dùng ảnh đó** — đổi
qua đổi lại thoải mái, không mất ảnh cũ. Ảnh mới tải lên được dùng luôn.

**Chữ** sửa được: tên lớn, dòng nghề nghiệp, tiêu đề và đoạn giới thiệu, chữ
trên các nút và link của chúng, danh sách kỹ năng (thêm/bớt dòng, đổi icon),
tiêu đề và mô tả phần khách hàng.

**Thứ tự các khối**: kéo thả để đổi, bỏ tick để ẩn hẳn một khối khỏi trang.

Trong ô nhập nhiều dòng, xuống dòng sẽ thành ngắt dòng trên web.

---

## Bố cục 2 lớn + 3 nhỏ

Trang portfolio xếp theo nhịp lặp: 2 thẻ lớn, rồi 3 thẻ nhỏ, rồi lại 2 lớn…

App tính kích thước thẻ **theo vị trí** chứ không theo ô tick từng project, nên
kéo thả đổi thứ tự xong nhịp vẫn khớp. Bấm **+ Project mới** là tạo trọn một
khối 5 cái — hộp thoại ghi rõ cái nào sẽ ra thẻ lớn, cái nào thẻ nhỏ.

Muốn tự quyết từng thẻ: vào **Giao diện → Bố cục lưới project**, tắt "Tự động
lặp". Cũng chỗ đó đổi được số thẻ lớn / nhỏ mỗi khối.

---

## Giao diện (màu sắc, chữ, bố cục)

Tab **Giao diện** trên thanh trên. Chỉnh gì cũng thấy ngay ở khung xem trước
bên phải — xem được cả 3 trang và 3 cỡ màn hình, chưa lưu thì web thật chưa đổi.

| Nhóm | Chỉnh được |
|---|---|
| Bố cục lưới | bật/tắt nhịp tự động, số thẻ lớn - nhỏ mỗi khối |
| Màu sắc | 17 màu: nền, màu nhấn, các cấp độ chữ, viền |
| Chữ | phông chính và phông dự phòng |
| Kích thước | bề ngang nội dung, bo góc, khoảng cách thẻ, tỉ lệ khung ảnh |

**Tỉ lệ khung ảnh** viết dạng `rộng / cao`. Muốn ảnh bìa không bị cắt thì điền
đúng kích thước file gốc — thẻ lớn đang để `4500 / 3519` khớp với ảnh bìa thật,
nên hiện nguyên khung không mất phần nào. Thẻ lớn dùng chung một tỉ lệ ở mọi
khổ màn hình; thẻ nhỏ có ô riêng cho điện thoại.

**Bề ngang ảnh trong project** quyết định độ rộng của mọi ảnh trong trang chi
tiết. Mọi ảnh dùng chung một số nên mép trái - phải luôn thẳng hàng từ trên
xuống, bất kể ảnh ngang, vuông hay dọc. Để 100% là dùng trọn bề ngang; giảm
xuống 80% chẳng hạn thì cả cột ảnh thu vào nhưng vẫn thẳng hàng.

Bấm **Lưu giao diện** để ghi ra `css/theme.css`, hoặc **Về mặc định** để quay
lại bản gốc. Ảnh và project không bị ảnh hưởng.

> Đổi phông chữ thì nhớ sửa cả link Google Fonts trong 3 file .html, không thì
> trình duyệt dùng phông dự phòng.

---

## Trong app làm được gì

| Nút | Việc |
|---|---|
| Kéo thả thẻ project | đổi thứ tự hiện trên trang portfolio |
| **Sửa** | mở màn chỉnh tên, danh mục, mô tả, thẻ rộng/hẹp |
| Kéo thả ô ảnh | đổi thứ tự ảnh trong project |
| **⭐ Bìa** | chọn ảnh làm thumbnail ngoài trang portfolio |
| **🚫 Ẩn** | giữ file trong thư mục nhưng không hiện trên web |
| **🗑** | xóa ảnh (chuyển vào `admin/_trash/`, vẫn lấy lại được) |
| **+ Thêm ảnh** / kéo file vào | copy ảnh từ máy vào thư mục project |
| **+ Project mới** | tạo thư mục + project mới |
| **Mở thư mục** | mở thư mục project trong Explorer / Finder |
| **Xem thử web** | mở trang portfolio thật đang chạy trên localhost |
| **Đăng lên web** | `git add` + `commit` + `push` — thay cho GitHub Desktop |
| **Tắt app** | dừng máy chủ localhost |

---

## Xóa nhầm thì sao

Mọi thứ bị xóa đều nằm trong `admin/_trash/<ngày-giờ>/`.
Kéo ngược lại vào thư mục project rồi bấm **Quét lại thư mục** là xong.
Thư mục này không được đẩy lên GitHub.

## Nếu "Đăng lên web" báo lỗi

App sẽ hiện nguyên văn lỗi của git. Trường hợp hay gặp:

- **push bị từ chối / hỏi đăng nhập** → đăng nhập GitHub một lần
  (Windows: mở GitHub Desktop bấm Push; macOS: làm theo hướng dẫn hiện trong
  Terminal hoặc trình duyệt). Các lần sau app tự push được.
- **đã commit nhưng chưa push** → mở GitHub Desktop, bấm **Push origin**.

---

## Chạy tay bằng dòng lệnh

```bash
py -3 admin/server.py          # Windows: mở app
admin/.venv/bin/python3 admin/server.py   # macOS: mở app
py -3 admin/make_icon.py       # dựng lại icon
py -3 admin/migrate.py         # xem trước việc gom ảnh vào thư mục (đã chạy 1 lần)
```

Đổi cổng nếu 4321 bị chiếm: đặt biến môi trường `PORTFOLIO_ADMIN_PORT`.
