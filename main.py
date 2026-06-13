from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.config import AppConfig, ensure_directories
from src.processor import VideoProcessor
from src.tiktok.auth import TikTokAuth
from src.watcher import FolderWatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
config = AppConfig(BASE_DIR)
auth = TikTokAuth(config)
processor = VideoProcessor(config)
watcher: FolderWatcher | None = None
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global watcher
    ensure_directories(config)
    loop = asyncio.get_running_loop()
    watcher = FolderWatcher(config, processor, loop)
    watcher.start()
    asyncio.create_task(watcher.scan_existing())
    logger.info("TikTok Auto Poster 起動完了")
    yield
    if watcher:
        watcher.stop()


app = FastAPI(title="TikTok Auto Poster", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = auth.load_token()
    jobs = processor.store.list_recent(30)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "configured": auth.is_configured(),
            "authenticated": auth.is_authenticated(),
            "open_id": token.open_id if token else "",
            "watch_folder": str(config.watch_folder),
            "post_mode": config.post_mode,
            "privacy_level": config.privacy_level,
            "jobs": jobs,
        },
    )


@app.get("/auth/login")
async def auth_login():
    if not auth.is_configured():
        raise HTTPException(400, "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET を .env に設定してください")
    url, _ = auth.build_auth_url()
    return RedirectResponse(url)


@app.get("/callback")
async def auth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(400, f"TikTok認証エラー: {error}")
    if not code or not state or not auth.validate_state(state):
        raise HTTPException(400, "無効な認証応答です")
    await auth.exchange_code(code)
    return RedirectResponse("/", status_code=303)


@app.post("/auth/logout")
async def auth_logout():
    path = config.token_path
    if path.exists():
        path.unlink()
    return RedirectResponse("/", status_code=303)


@app.get("/api/status")
async def api_status():
    token = auth.load_token()
    return {
        "configured": auth.is_configured(),
        "authenticated": auth.is_authenticated(),
        "watch_folder": str(config.watch_folder),
        "post_mode": config.post_mode,
        "open_id": token.open_id if token else None,
    }


@app.get("/api/jobs")
async def api_jobs():
    return processor.store.list_recent(50)


@app.post("/scan")
async def scan_folder():
    if watcher is None:
        raise HTTPException(503, "Watcher not ready")
    asyncio.create_task(watcher.scan_existing())
    return RedirectResponse("/", status_code=303)


@app.post("/api/scan")
async def api_scan():
    if watcher is None:
        raise HTTPException(503, "Watcher not ready")
    asyncio.create_task(watcher.scan_existing())
    return {"ok": True, "message": "フォルダスキャンを開始しました"}
