#!/bin/bash
# ============================================================
#  Cài Portfolio Manager lên macOS
#
#  Cách dùng: bấm đúp vào file này trong Finder.
#  Nếu macOS không cho chạy: mở Terminal, gõ
#      chmod +x "đường dẫn tới install-mac.command"
#  rồi bấm đúp lại.
# ============================================================

set -u

APP_NAME="Portfolio Manager"
REPO_URL="https://github.com/tiev84/portfolio-tiev.git"
DEFAULT_DIR="$HOME/Documents/portfolio-tiev"

say()  { printf '\n\033[1;33m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[0;32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[0;33m!\033[0m %s\n' "$*"; }
die()  { printf '\n\033[0;31m✗ %s\033[0m\n\n' "$*"; read -r -p "Nhấn Enter để đóng..." _; exit 1; }

printf '\n\033[1m============================================================\033[0m\n'
printf '\033[1m  CÀI ĐẶT PORTFOLIO MANAGER (macOS)\033[0m\n'
printf '\033[1m============================================================\033[0m\n'

# ------------------------------------------------------------
# 1. Công cụ bắt buộc
# ------------------------------------------------------------
say "[1/6] Kiểm tra công cụ"

command -v git >/dev/null 2>&1 || die "Chưa có git.
Mở Terminal, gõ lệnh sau rồi bấm Install, xong chạy lại file này:
    xcode-select --install"
ok "git"

PYTHON=""
for candidate in python3 /usr/local/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PYTHON="$(command -v "$candidate")"
    break
  fi
done
[ -n "$PYTHON" ] || die "Chưa có Python 3.9 trở lên.
Cách 1: chạy  xcode-select --install
Cách 2: tải tại https://www.python.org/downloads/macos/"
ok "python3 ($("$PYTHON" -V 2>&1))"

if command -v git-lfs >/dev/null 2>&1; then
  ok "git-lfs"
  git lfs install --skip-repo >/dev/null 2>&1
else
  warn "Chưa có git-lfs — file video .mp4 sẽ tải về dạng rút gọn, không xem được."
  warn "Muốn có video: cài Homebrew rồi chạy  brew install git-lfs"
fi

# ------------------------------------------------------------
# 2. Repo
# ------------------------------------------------------------
say "[2/6] Tìm thư mục portfolio"

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$HERE/portfolio.html" ] && [ -d "$HERE/admin" ]; then
  REPO="$HERE"
  ok "Đang chạy sẵn trong repo: $REPO"
elif [ -f "$DEFAULT_DIR/portfolio.html" ]; then
  REPO="$DEFAULT_DIR"
  ok "Đã có sẵn: $REPO"
  git -C "$REPO" pull --ff-only >/dev/null 2>&1 && ok "Đã cập nhật bản mới nhất" || warn "Không pull được (có thay đổi chưa lưu?) — bỏ qua."
else
  printf '\n  Chưa có portfolio trên máy này. Sẽ tải về từ GitHub.\n'
  printf '  Thư mục [%s]: ' "$DEFAULT_DIR"
  read -r ANSWER </dev/tty
  REPO="${ANSWER:-$DEFAULT_DIR}"
  REPO="${REPO/#\~/$HOME}"
  mkdir -p "$(dirname "$REPO")" || die "Không tạo được $(dirname "$REPO")"
  git clone "$REPO_URL" "$REPO" || die "Tải repo thất bại. Kiểm tra mạng rồi thử lại."
  ok "Đã tải về: $REPO"
fi

[ -f "$REPO/admin/server.py" ] || die "Thư mục $REPO thiếu admin/server.py — có vẻ chưa phải bản mới."

# ------------------------------------------------------------
# 3. Môi trường Python riêng
# ------------------------------------------------------------
say "[3/6] Cài thư viện"

VENV="$REPO/admin/.venv"
if [ ! -x "$VENV/bin/python3" ]; then
  "$PYTHON" -m venv "$VENV" || die "Không tạo được môi trường Python tại $VENV"
fi
"$VENV/bin/python3" -m pip install --quiet --upgrade pip >/dev/null 2>&1
if "$VENV/bin/python3" -m pip install --quiet Pillow; then
  ok "Pillow"
else
  warn "Không cài được Pillow — app vẫn chạy, chỉ là ảnh xem trước sẽ nặng."
fi

# ------------------------------------------------------------
# 4. Icon
# ------------------------------------------------------------
say "[4/6] Tạo icon"

"$VENV/bin/python3" "$REPO/admin/make_icon.py" >/dev/null 2>&1 || warn "Không dựng lại được icon.png, dùng bản có sẵn."

ICON_PNG="$REPO/admin/ui/icon.png"
ICNS="$REPO/admin/ui/icon.icns"

if [ -f "$ICON_PNG" ] && command -v iconutil >/dev/null 2>&1; then
  ICONSET="$(mktemp -d)/icon.iconset"
  mkdir -p "$ICONSET"
  for size in 16 32 64 128 256 512; do
    sips -z $size $size "$ICON_PNG" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null 2>&1
    double=$((size * 2))
    sips -z $double $double "$ICON_PNG" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null 2>&1
  done
  iconutil -c icns "$ICONSET" -o "$ICNS" >/dev/null 2>&1 && ok "icon.icns" || warn "Không tạo được .icns"
  rm -rf "$(dirname "$ICONSET")"
else
  warn "Bỏ qua icon (thiếu icon.png hoặc iconutil)"
fi

# ------------------------------------------------------------
# 5. Tạo app
# ------------------------------------------------------------
say "[5/6] Tạo ứng dụng"

APP_DIR="/Applications/$APP_NAME.app"
if ! mkdir -p "$APP_DIR/Contents/MacOS" 2>/dev/null; then
  APP_DIR="$HOME/Applications/$APP_NAME.app"
  mkdir -p "$APP_DIR/Contents/MacOS" || die "Không tạo được app ở /Applications lẫn ~/Applications"
  warn "Không ghi được vào /Applications — đặt ở ~/Applications"
fi
mkdir -p "$APP_DIR/Contents/Resources"

cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>              <string>$APP_NAME</string>
  <key>CFBundleDisplayName</key>       <string>$APP_NAME</string>
  <key>CFBundleIdentifier</key>        <string>com.tiev.portfoliomanager</string>
  <key>CFBundleVersion</key>           <string>1.0</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundlePackageType</key>       <string>APPL</string>
  <key>CFBundleExecutable</key>        <string>launcher</string>
  <key>CFBundleIconFile</key>          <string>icon</string>
  <key>NSHighResolutionCapable</key>   <true/>
</dict>
</plist>
PLIST

cat > "$APP_DIR/Contents/MacOS/launcher" <<LAUNCHER
#!/bin/bash
# Tự tạo bởi install-mac.command — chạy lại trình cài đặt nếu đổi chỗ thư mục.
REPO="$REPO"
PY="$VENV/bin/python3"
[ -x "\$PY" ] || PY="$PYTHON"
cd "\$REPO" || exit 1
exec "\$PY" "\$REPO/admin/server.py"
LAUNCHER

chmod +x "$APP_DIR/Contents/MacOS/launcher"
[ -f "$ICNS" ] && cp "$ICNS" "$APP_DIR/Contents/Resources/icon.icns"

# Bắt Finder đọc lại icon
touch "$APP_DIR"
ok "$APP_DIR"

ln -sfn "$APP_DIR" "$HOME/Desktop/$APP_NAME.app" 2>/dev/null && ok "Đã đặt icon trên Desktop"

# ------------------------------------------------------------
# 6. Thông tin git
# ------------------------------------------------------------
say "[6/6] Kiểm tra git"

if [ -z "$(git -C "$REPO" config user.email || true)" ]; then
  git -C "$REPO" config user.name "dangkimanh01"
  git -C "$REPO" config user.email "anhdangkim962@gmail.com"
  ok "Đã đặt tên người commit"
else
  ok "Đã có tên người commit: $(git -C "$REPO" config user.name)"
fi
warn 'Lần đầu bấm "Đăng lên web", GitHub sẽ hỏi đăng nhập trong Terminal hoặc trình duyệt.'

printf '\n\033[1m============================================================\033[0m\n'
printf '\033[1m  XONG\033[0m\n'
printf '  Portfolio  : %s\n' "$REPO"
printf '  Ứng dụng   : %s\n' "$APP_DIR"
printf '  Mở app     : bấm icon "%s" trên Desktop hoặc trong Launchpad\n' "$APP_NAME"
printf '\033[1m============================================================\033[0m\n\n'

read -r -p "Mở app luôn bây giờ? [Y/n] " RUN </dev/tty
case "${RUN:-Y}" in
  [Nn]*) ;;
  *) open "$APP_DIR" ;;
esac
