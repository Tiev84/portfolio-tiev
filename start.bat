@echo off
title Portfolio Manager - Tiev
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "admin\server.py"
) else (
  python "admin\server.py"
)

echo.
echo ============================================================
echo   App da tat. Nhan phim bat ky de dong cua so nay.
echo ============================================================
pause >nul
