@echo off
chcp 65001 >nul
title Cai dat Portfolio Manager
cd /d "%~dp0"

echo ============================================================
echo   CAI DAT PORTFOLIO MANAGER (Windows)
echo ============================================================
echo.

rem ---- 1. Tim Python -------------------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [X] Chua co Python.
  echo     Tai o https://www.python.org/downloads/  ^(nho tick "Add Python to PATH"^)
  echo.
  pause
  exit /b 1
)
echo [1/3] Python: OK

rem ---- 2. Pillow -----------------------------------------------------
%PY% -c "import PIL" >nul 2>nul
if errorlevel 1 (
  echo [2/3] Dang cai Pillow...
  %PY% -m pip install --quiet --disable-pip-version-check Pillow
  if errorlevel 1 (
    echo     [!] Cai Pillow that bai. App van chay duoc, chi la anh xem truoc se nang.
  )
) else (
  echo [2/3] Pillow: OK
)

rem ---- 3. Icon + shortcut --------------------------------------------
%PY% "admin\make_icon.py"
powershell -NoProfile -ExecutionPolicy Bypass -File "admin\install_windows.ps1"
if errorlevel 1 (
  echo [X] Khong tao duoc shortcut.
  pause
  exit /b 1
)
echo [3/3] Icon Desktop: OK

echo ============================================================
echo   XONG. Tim icon "Portfolio Manager" tren Desktop.
echo ============================================================
echo.
pause
