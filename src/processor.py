from __future__ import annotations

import asyncio
import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.config import AppConfig, build_caption, ensure_directories, load_video_metadata
from src.tiktok.auth import TikTokAuth
from src.tiktok.client import TikTokClient

logger = logging.getLogger(__name__)


class JobStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    caption TEXT,
                    status TEXT NOT NULL,
                    publish_id TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, file_path: str, caption: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO jobs (file_path, caption, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (file_path, caption, "pending", now, now),
            )
            return int(cur.lastrowid)

    def update(
        self,
        job_id: int,
        status: str,
        publish_id: str | None = None,
        error: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE jobs SET status=?, publish_id=?, error=?, updated_at=?
                WHERE id=?
                """,
                (status, publish_id, error, now, job_id),
            )

    def list_recent(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


class VideoProcessor:
    def __init__(self, config: AppConfig):
        self.config = config
        self.auth = TikTokAuth(config)
        self.client = TikTokClient(config, self.auth)
        self.store = JobStore(config.db_path)
        self._processing: set[str] = set()
        self._lock = asyncio.Lock()

    async def wait_until_stable(self, path: Path) -> bool:
        wait = self.config.stable_wait_seconds
        if wait <= 0:
            return True
        try:
            last_size = path.stat().st_size
        except OSError:
            return False
        await asyncio.sleep(wait)
        try:
            return path.exists() and path.stat().st_size == last_size and last_size > 0
        except OSError:
            return False

    async def process_file(self, video_path: Path) -> None:
        key = str(video_path.resolve())
        async with self._lock:
            if key in self._processing:
                return
            self._processing.add(key)

        try:
            if not video_path.exists():
                return
            if video_path.suffix.lower() not in self.config.video_extensions:
                return
            if not await self.wait_until_stable(video_path):
                logger.warning("ファイルが安定しませんでした: %s", video_path)
                return

            metadata = load_video_metadata(video_path)
            caption = build_caption(self.config, video_path, metadata)
            job_id = self.store.create(str(video_path), caption)
            logger.info("投稿開始: %s", video_path.name)

            try:
                result = await self.client.publish(video_path, caption)
                if result.status in ("PUBLISH_COMPLETE", "SENT_TO_USER_INBOX"):
                    self.store.update(job_id, "success", result.publish_id)
                    logger.info("投稿成功: %s (%s)", video_path.name, result.status)
                    self._move_file(video_path, self.config.processed_folder)
                else:
                    msg = result.fail_reason or result.status
                    self.store.update(job_id, "failed", result.publish_id, msg)
                    logger.error("投稿失敗: %s — %s", video_path.name, msg)
                    self._move_file(video_path, self.config.failed_folder)
            except Exception as exc:
                self.store.update(job_id, "failed", error=str(exc))
                logger.exception("投稿エラー: %s", video_path.name)
                self._move_file(video_path, self.config.failed_folder)
        finally:
            async with self._lock:
                self._processing.discard(key)

    def _move_file(self, video_path: Path, dest_dir: Path | None) -> None:
        if dest_dir is None:
            return
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / video_path.name
        if target.exists():
            stem = video_path.stem
            suffix = video_path.suffix
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = dest_dir / f"{stem}_{ts}{suffix}"
        shutil.move(str(video_path), str(target))
        for meta in (video_path.with_suffix(video_path.suffix + ".meta.json"), video_path.with_suffix(".json")):
            if meta.exists():
                shutil.move(str(meta), str(dest_dir / meta.name))
