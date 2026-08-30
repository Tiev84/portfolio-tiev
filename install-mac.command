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
die()  { printf '\n\033[0;31m✗ %s\033[0m\n\n' "$*"; ask "Nhấn Enter để đóng..." "" >/dev/null; exit 1; }

# Hỏi người dùng một câu. Chạy bằng cách bấm đúp trong Finder thì có bàn phím
# (/dev/tty); chạy trong script tự động thì không — lúc đó lấy giá trị mặc định.
ask() {
  __prompt="$1"; __default="${2-}"; __reply=""
  if { : > /dev/tty; } 2>/dev/null; then
    printf '%s' "$__prompt" > /dev/tty 2>/dev/null
    read -r __reply < /dev/tty 2>/dev/null || __reply=""
  fi
  printf '%s' "${__reply:-$__default}"
}

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

# File .mp4 trong repo lưu bằng git-lfs. Nếu máy chưa có git-lfs thì git sẽ
# CHẾT giữa lúc checkout ("git-lfs: command not found" -> clone hỏng), nên phải
# tắt hẳn bộ lọc lfs. Lúc đó file video chỉ là con trỏ vài trăm byte, còn mọi
# thứ khác tải về đầy đủ.
LFS_OFF=""
if command -v git-lfs >/dev/null 2>&1; then
  ok "git-lfs"
  git lfs install --skip-repo >/dev/null 2>&1
else
  LFS_OFF="-c filter.lfs.smudge= -c filter.lfs.clean= -c filter.lfs.process= -c filter.lfs.required=false"
  warn "Chưa có git-lfs — bỏ qua file video .mp4, phần còn lại vẫn đủ."
  warn "Muốn có video: cài Homebrew rồi chạy  brew install git-lfs, sau đó chạy lại file này."
fi

# ------------------------------------------------------------
# 2. Repo
# ------------------------------------------------------------
say "[2/6] Tìm thư mục portfolio"

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$HERE/portfolio.html" ] && [ -d "$HERE/admin" ]; then
  REPO="$HERE"
  ok "Đang chạy sẵn trong repo: $REPO"
elif [ -d "$DEFAULT_DIR/.git" ]; then
  REPO="$DEFAULT_DIR"
  ok "Đã có sẵn: $REPO"
else
  printf '\n  Chưa có portfolio trên máy này. Sẽ tải về từ GitHub.\n'
  REPO="$(ask "  Thư mục [$DEFAULT_DIR]: " "$DEFAULT_DIR")"
  REPO="${REPO/#\~/$HOME}"

  if [ -d "$REPO/.git" ]; then
    ok "Đã có sẵn: $REPO"
  else
    mkdir -p "$(dirname "$REPO")" || die "Không tạo được $(dirname "$REPO")"
    git $LFS_OFF clone "$REPO_URL" "$REPO" || die "Tải repo thất bại. Kiểm tra mạng rồi thử lại."
    ok "Đã tải về: $REPO"
  fi
fi

# Lấy bản mới nhất. Bỏ qua nếu đang có thay đổi chưa lưu — không giẫm lên chúng.
if [ -z "$(git -C "$REPO" status --porcelain 2>/dev/null)" ]; then
  git $LFS_OFF -C "$REPO" pull --ff-only >/dev/null 2>&1 && ok "Đã cập nhật bản mới nhất"
fi

# Cứu trường hợp lần trước clone xong nhưng checkout dở dang (thiếu git-lfs).
if [ ! -f "$REPO/portfolio.html" ] || [ ! -f "$REPO/admin/server.py" ]; then
  warn "Thư mục thiếu file — đang ghi lại từ bản đã tải…"
  git $LFS_OFF -C "$REPO" checkout -f HEAD >/dev/null 2>&1 || true
fi

[ -f "$REPO/admin/server.py" ] || die "Thư mục $REPO vẫn thiếu admin/server.py.
Xoá thư mục đó đi rồi chạy lại file này:
    rm -rf \"$REPO\""

# Có git-lfs thì kéo nội dung video thật về (thay cho file con trỏ).
if command -v git-lfs >/dev/null 2>&1; then
  git -C "$REPO" lfs pull >/dev/null 2>&1 && ok "Đã tải file video" || warn "Không tải được file video (bỏ qua)"
fi

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

# ---- Shortcut trên Desktop ----
# Ưu tiên alias thật của Finder (hiện đúng icon, bấm đúp là chạy).
# Không được thì lùi về liên kết tượng trưng.
ALIAS_PATH="$HOME/Desktop/$APP_NAME"

[ -L "$ALIAS_PATH.app" ] && rm -f "$ALIAS_PATH.app"
[ -L "$ALIAS_PATH" ] && rm -f "$ALIAS_PATH"
# alias cũ là file thường — xoá để tạo lại; thư mục thật thì không đụng tới
if [ -e "$ALIAS_PATH" ] && [ ! -d "$ALIAS_PATH" ]; then rm -f "$ALIAS_PATH"; fi

if osascript -e "tell application \"Finder\" to make alias file to POSIX file \"$APP_DIR\" at POSIX file \"$HOME/Desktop\"" >/dev/null 2>&1; then
  # Finder đặt tên kèm chữ "alias" — đổi lại cho gọn
  [ -e "$HOME/Desktop/$APP_NAME alias" ] && mv -f "$HOME/Desktop/$APP_NAME alias" "$ALIAS_PATH"
  ok "Shortcut trên Desktop"
elif ln -sfn "$APP_DIR" "$ALIAS_PATH.app"; then
  ok "Shortcut trên Desktop (dạng liên kết)"
else
  warn "Không đặt được shortcut trên Desktop — mở app từ Launchpad cũng được."
fi

# ------------------------------------------------------------
# 6. Thông tin git
# ------------------------------------------------------------
say "[6/6] Kiểm tra git"

if [ -z "$(git -C "$REPO" config user.email 2>/dev/null || true)" ]; then
  if git -C "$REPO" config user.name "dangkimanh01" 2>/dev/null &&
     git -C "$REPO" config user.email "anhdangkim962@gmail.com" 2>/dev/null; then
    ok "Đã đặt tên người commit"
  else
    warn "Không đặt được tên người commit — git sẽ hỏi khi đăng lên web lần đầu."
  fi
else
  ok "Đã có tên người commit: $(git -C "$REPO" config user.name 2>/dev/null)"
fi
warn 'Lần đầu bấm "Đăng lên web", GitHub sẽ hỏi đăng nhập trong Terminal hoặc trình duyệt.'

printf '\n\033[1m============================================================\033[0m\n'
printf '\033[1m  XONG\033[0m\n'
printf '  Portfolio  : %s\n' "$REPO"
printf '  Ứng dụng   : %s\n' "$APP_DIR"
printf '  Mở app     : bấm icon "%s" trên Desktop hoặc trong Launchpad\n' "$APP_NAME"
printf '\033[1m============================================================\033[0m\n\n'

RUN="$(ask "Mở app luôn bây giờ? [Y/n] " "Y")"
case "$RUN" in
  [Nn]*) printf '\nMở sau bằng icon "%s" trên Desktop.\n\n' "$APP_NAME" ;;
  *) open "$APP_DIR" ;;
esac
