@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".env" (
  echo .env が見つかりません。.env.example をコピーして設定してください。
  copy .env.example .env
  pause
  exit /b 1
)

if not exist "venv" (
  echo Python 仮想環境を作成中...
  python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q

if not exist "watch" mkdir watch
if not exist "config.yaml" copy config.yaml.example config.yaml

echo.
echo ========================================
echo  TikTok 時間予告 自動投稿アプリ
echo  http://127.0.0.1:8765 を開いてください
echo ========================================
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 8765
