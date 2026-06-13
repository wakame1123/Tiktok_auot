from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.config import AppConfig
from src.processor import VideoProcessor

logger = logging.getLogger(__name__)


class VideoEventHandler(FileSystemEventHandler):
    def __init__(self, config: AppConfig, processor: VideoProcessor, loop: asyncio.AbstractEventLoop):
        self.config = config
        self.processor = processor
        self.loop = loop

    def _schedule(self, path: Path) -> None:
        if path.suffix.lower() not in self.config.video_extensions:
            return
        if path.parent.name in ("processed", "failed"):
            return
        asyncio.run_coroutine_threadsafe(self.processor.process_file(path), self.loop)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._schedule(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._schedule(Path(event.dest_path))


class FolderWatcher:
    def __init__(self, config: AppConfig, processor: VideoProcessor, loop: asyncio.AbstractEventLoop):
        self.config = config
        self.processor = processor
        self.loop = loop
        self.observer: Observer | None = None

    def start(self) -> None:
        folder = str(self.config.watch_folder)
        handler = VideoEventHandler(self.config, self.processor, self.loop)
        self.observer = Observer()
        self.observer.schedule(handler, folder, recursive=False)
        self.observer.start()
        logger.info("監視開始: %s", folder)

    def stop(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None
            logger.info("監視停止")

    async def scan_existing(self) -> None:
        folder = self.config.watch_folder
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.suffix.lower() in self.config.video_extensions:
                await self.processor.process_file(path)
