@echo off
REM Windows 下直接双击运行（需要先装 Python 3.9+）
REM 数据会存在这个文件夹里的 data.db

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo 没找到 python。
  echo 请先装 Python 3.9 或更高： https://www.python.org/downloads/
  echo 安装时记得勾上 "Add Python to PATH"
  pause
  exit /b 1
)

echo.
echo   去往未来 正在启动...
echo   地址:  http://127.0.0.1:9000
echo   密码:  weilai2026      （登录后在「设置」里改）
echo.
echo   按 Ctrl+C 可以停掉。
echo.

python app.py
pause
