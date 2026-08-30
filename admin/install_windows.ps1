# Tạo icon "Portfolio Manager" trên Desktop (Windows).
# Đừng chạy file này trực tiếp — bấm install-windows.bat ở gốc repo.

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$ico = Join-Path $repo "admin\ui\app.ico"
$target = Join-Path $repo "start.bat"

if (-not (Test-Path $target)) {
  throw "Khong thay start.bat trong $repo"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$link = Join-Path $desktop "Portfolio Manager.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($link)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $repo
$shortcut.Description = "Quan ly anh cho portfolio-tiev"
$shortcut.WindowStyle = 7          # cua so console chay thu nho
if (Test-Path $ico) { $shortcut.IconLocation = "$ico,0" }
$shortcut.Save()

Write-Output ""
Write-Output "  Da tao icon: $link"
Write-Output "  Repo       : $repo"
Write-Output ""
