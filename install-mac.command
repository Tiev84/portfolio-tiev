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

# Chạy một lệnh nhưng không cho nó treo quá lâu.
# macOS không có sẵn lệnh `timeout`, nên phải tự canh: chạy nền, đếm giây,
# quá hạn thì giết. Không có cái này thì một lệnh git gặp mạng bị chặn sẽ
# ngồi im hàng phút, người dùng nhìn màn hình đứng chẳng biết chuyện gì.
run_limited() {
  __limit="$1"; shift
  "$@" >/dev/null 2>&1 &
  __pid=$!
  __waited=0
  while kill -0 "$__pid" 2>/dev/null; do
    sleep 1
    __waited=$((__waited + 1))
    if [ "$__waited" -ge "$__limit" ]; then
      kill -9 "$__pid" 2>/dev/null
      wait "$__pid" 2>/dev/null
      return 124
    fi
  done
  wait "$__pid"
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

# Lấy bản mới nhất. Đây là bước KHÔNG bắt buộc: mạng chặn github.com thì bỏ
# qua, cài tiếp bằng bản đang có trên máy. GIT_TERMINAL_PROMPT=0 để git khỏi
# ngồi chờ mật khẩu mà không hiện ô nhập.
if [ -z "$(git -C "$REPO" status --porcelain 2>/dev/null)" ]; then
  printf '    đang hỏi GitHub xem có bản mới không (tối đa 25 giây)...\n'
  if GIT_TERMINAL_PROMPT=0 run_limited 25 git $LFS_OFF -C "$REPO" pull --ff-only; then
    ok "Đã cập nhật bản mới nhất"
  else
    warn "Không hỏi được GitHub (mạng chậm hoặc bị chặn) — dùng bản đang có."
  fi
else
  warn "Thư mục có thay đổi chưa lưu — bỏ qua bước cập nhật."
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
  # Video 138 MB, mạng chậm tải lâu là bình thường — để rộng tay, đừng cắt
  # nhầm lúc nó đang tải thật.
  printf '    đang tải file video, có thể lâu (tối đa 5 phút)...\n'
  if GIT_TERMINAL_PROMPT=0 run_limited 300 git -C "$REPO" lfs pull; then
    ok "Đã tải file video"
  else
    warn "Không tải được file video (bỏ qua) — phần còn lại vẫn đủ."
  fi
fi

# ------------------------------------------------------------
# 3. Môi trường Python riêng
# ------------------------------------------------------------
say "[3/6] Cài thư viện"

printf '    lần đầu cài hơi lâu, khoảng 1-2 phút...\n'

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

# --if-missing: icon đã có trong repo thì để nguyên, tránh làm repo bẩn
"$VENV/bin/python3" "$REPO/admin/make_icon.py" --if-missing >/dev/null 2>&1 ||
  warn "Không dựng lại được icon.png, dùng bản có sẵn."

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

LOG_PATH="$HOME/Library/Logs/PortfolioManager.log"
mkdir -p "$HOME/Library/Logs" 2>/dev/null || true

# App được dựng bằng osacompile — công cụ có sẵn của macOS. Bundle do Apple
# sinh ra thì Finder/Gatekeeper luôn chấp nhận, chắc ăn hơn tự tạo thư mục
# .app bằng tay (cách cũ có máy bấm vào không chạy).
# mktemp -t <prefix> chỉ chạy trên macOS; mktemp -d thì hệ nào cũng hiểu
SCRIPT_SRC="$(mktemp -d)/portfoliomgr.applescript"

cat > "$SCRIPT_SRC" <<'APPLESCRIPT'
-- Portfolio Manager — do install-mac.command tạo tự động.
-- Nhiệm vụ duy nhất: mở start-mac.command trong Terminal.
-- Chạy trong Terminal (thay vì chạy ngầm) để lỗi hiện ra trước mắt,
-- giống hệt cửa sổ đen của bản Windows.

set repoPath to "__REPO__"
set starterPath to repoPath & "/start-mac.command"

on failWith(msg)
	display alert "Portfolio Manager không chạy được" message msg as critical
end failWith

-- Thư mục portfolio còn nguyên không?
try
	do shell script "test -f " & quoted form of (repoPath & "/admin/server.py")
on error
	failWith("Không thấy portfolio ở:" & return & repoPath & return & return & "Có thể thư mục đã bị đổi tên hoặc xoá. Chạy lại install-mac.command để sửa.")
	return
end try

-- File khởi động còn không?
try
	do shell script "test -x " & quoted form of starterPath
on error
	failWith("Thiếu file khởi động:" & return & starterPath & return & return & "Chạy lại install-mac.command để tạo lại.")
	return
end try

-- open -a Terminal không cần xin quyền điều khiển ứng dụng, khác với
-- \"tell application Terminal\" — nên chạy được ngay từ lần đầu.
try
	do shell script "/usr/bin/open -a Terminal " & quoted form of starterPath
on error errMsg
	failWith("Không mở được Terminal." & return & return & errMsg)
end try
APPLESCRIPT

# Nhét đường dẫn thật vào (dùng | làm dấu phân cách để khỏi vướng dấu /)
sed -i '' \
  -e "s|__REPO__|$REPO|g" \
  -e "s|__PY__|$VENV/bin/python3|g" \
  -e "s|__LOG__|$LOG_PATH|g" \
  -e "s|__PORT__|4321|g" \
  "$SCRIPT_SRC" 2>/dev/null || sed -i \
  -e "s|__REPO__|$REPO|g" \
  -e "s|__PY__|$VENV/bin/python3|g" \
  -e "s|__LOG__|$LOG_PATH|g" \
  -e "s|__PORT__|4321|g" \
  "$SCRIPT_SRC"

# Phương án cứu hộ, tạo TRƯỚC: file bấm đúp chạy trong Terminal. Luôn hoạt động
# kể cả khi bundle .app gặp trục trặc.
cat > "$REPO/start-mac.command" <<STARTER
#!/bin/bash
# Mở Portfolio Manager. Tạo tự động bởi install-mac.command.
# Cửa sổ Terminal này chính là "máy chủ" — đóng nó là app tắt.

cd "$REPO" || { echo "Không mở được thư mục: $REPO"; read -r _; exit 1; }

PY="$VENV/bin/python3"
[ -x "\$PY" ] || PY="\$(command -v python3)"
if [ -z "\$PY" ]; then
  echo "Không tìm thấy Python 3 trên máy."
  echo "Mở Terminal chạy:  xcode-select --install"
  read -r _
  exit 1
fi

"\$PY" admin/server.py
CODE=\$?

if [ \$CODE -ne 0 ]; then
  echo
  echo "============================================================"
  echo "  App dừng với mã lỗi \$CODE."
  echo "  Chụp màn hình cửa sổ này để biết nguyên nhân."
  echo "============================================================"
  read -r _
fi
STARTER
chmod +x "$REPO/start-mac.command"

APP_OK=0
APP_DIR="/Applications/$APP_NAME.app"
rm -rf "$APP_DIR" 2>/dev/null
if osacompile -o "$APP_DIR" "$SCRIPT_SRC" 2>/dev/null; then
  APP_OK=1
else
  APP_DIR="$HOME/Applications/$APP_NAME.app"
  mkdir -p "$HOME/Applications"
  rm -rf "$APP_DIR" 2>/dev/null
  if osacompile -o "$APP_DIR" "$SCRIPT_SRC" 2>/dev/null; then
    APP_OK=1
    warn "Không ghi được vào /Applications — đặt ở ~/Applications"
  else
    warn "Máy này không dựng được ứng dụng .app — dùng cách mở bằng Terminal."
  fi
fi
rm -f "$SCRIPT_SRC"

# ---- Dọn shortcut cũ trên Desktop ----
ALIAS_PATH="$HOME/Desktop/$APP_NAME"
[ -L "$ALIAS_PATH.app" ] && rm -f "$ALIAS_PATH.app"
[ -L "$ALIAS_PATH" ] && rm -f "$ALIAS_PATH"
[ -f "$ALIAS_PATH.command" ] && rm -f "$ALIAS_PATH.command"
# alias cũ là file thường — xoá để tạo lại; thư mục thật thì không đụng tới
if [ -e "$ALIAS_PATH" ] && [ ! -d "$ALIAS_PATH" ]; then rm -f "$ALIAS_PATH"; fi

if [ "$APP_OK" = "1" ]; then
  # ---- Hoàn thiện bundle: tên hiển thị + icon ----
  PLB=/usr/libexec/PlistBuddy
  if [ -x "$PLB" ]; then
    "$PLB" -c "Set :CFBundleName $APP_NAME" "$APP_DIR/Contents/Info.plist" 2>/dev/null || true
    "$PLB" -c "Add :CFBundleDisplayName string $APP_NAME" "$APP_DIR/Contents/Info.plist" 2>/dev/null ||
      "$PLB" -c "Set :CFBundleDisplayName $APP_NAME" "$APP_DIR/Contents/Info.plist" 2>/dev/null || true
    "$PLB" -c "Add :CFBundleIdentifier string com.tiev.portfoliomanager" "$APP_DIR/Contents/Info.plist" 2>/dev/null ||
      "$PLB" -c "Set :CFBundleIdentifier com.tiev.portfoliomanager" "$APP_DIR/Contents/Info.plist" 2>/dev/null || true
  fi

  # osacompile đặt tên icon mặc định là applet.icns — ghi đè bằng icon của mình
  [ -f "$ICNS" ] && cp -f "$ICNS" "$APP_DIR/Contents/Resources/applet.icns" 2>/dev/null

  touch "$APP_DIR"        # bắt Finder đọc lại icon
  LSREG="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
  [ -x "$LSREG" ] && "$LSREG" -f "$APP_DIR" >/dev/null 2>&1
  ok "$APP_DIR"

  # ---- Shortcut Desktop: alias thật của Finder ----
  if osascript -e "tell application \"Finder\" to make alias file to POSIX file \"$APP_DIR\" at POSIX file \"$HOME/Desktop\"" >/dev/null 2>&1; then
    [ -e "$HOME/Desktop/$APP_NAME alias" ] && mv -f "$HOME/Desktop/$APP_NAME alias" "$ALIAS_PATH"
    ok "Shortcut trên Desktop"
  else
    # Finder từ chối (thường do chưa cấp quyền Automation) — dùng file .command
    cp -f "$REPO/start-mac.command" "$ALIAS_PATH.command"
    chmod +x "$ALIAS_PATH.command"
    warn "Finder không cho tạo alias — đã đặt \"$APP_NAME.command\" trên Desktop thay thế."
    warn "App vẫn nằm trong Launchpad."
  fi
else
  # Không dựng được .app: đặt thẳng file .command ra Desktop, bấm đúp vẫn chạy.
  cp -f "$REPO/start-mac.command" "$ALIAS_PATH.command"
  chmod +x "$ALIAS_PATH.command"
  ok "Đã đặt \"$APP_NAME.command\" trên Desktop (mở kèm cửa sổ Terminal)"
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
# macOS không có sẵn trình nhớ mật khẩu cho git. Không đặt cái này thì lần
# nào đẩy lên GitHub cũng bị hỏi lại, mà app chạy nền nên không hỏi được.
if git -C "$REPO" config credential.helper osxkeychain 2>/dev/null; then
  ok "Đã bật ghi nhớ đăng nhập GitHub (Keychain)"
else
  warn "Không bật được ghi nhớ đăng nhập — mỗi lần đăng sẽ phải nhập lại."
fi

warn 'Lần đầu bấm "Đăng lên web", app sẽ mở Terminal để bạn đăng nhập GitHub một lần.'

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
