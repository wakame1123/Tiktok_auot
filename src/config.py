from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_redirect_uri: str = "http://127.0.0.1:8765/callback"
    watch_folder: str = "./watch"
    post_mode: str = "direct"
    privacy_level: str = "PUBLIC_TO_EVERYONE"
    caption_template: str = (
        "{title}\n\n{live_time} からLIVE配信します！\n"
        "リマインダー設定お願いします🙏\n\n{hashtags}"
    )
    default_hashtags: str = "TikTokLIVE,ライブ告知,時間予告"
    web_port: int = 8765


class AppConfig:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.settings = Settings()
        self.yaml_path = self.base_dir / "config.yaml"
        self._yaml: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        if self.yaml_path.exists():
            with self.yaml_path.open(encoding="utf-8") as f:
                self._yaml = yaml.safe_load(f) or {}
        else:
            self._yaml = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._yaml.get(key, default)

    @property
    def watch_folder(self) -> Path:
        raw = self.get("watch_folder") or self.settings.watch_folder
        path = Path(raw)
        if not path.is_absolute():
            path = self.base_dir / path
        return path

    @property
    def processed_folder(self) -> Path | None:
        raw = self.get("processed_folder")
        if not raw:
            return None
        path = Path(raw)
        if not path.is_absolute():
            path = self.base_dir / path
        return path

    @property
    def failed_folder(self) -> Path | None:
        raw = self.get("failed_folder")
        if not raw:
            return None
        path = Path(raw)
        if not path.is_absolute():
            path = self.base_dir / path
        return path

    @property
    def stable_wait_seconds(self) -> float:
        return float(self.get("stable_wait_seconds", 5))

    @property
    def video_extensions(self) -> set[str]:
        exts = self.get("video_extensions", [".mp4", ".mov", ".webm"])
        return {e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts}

    @property
    def post_mode(self) -> str:
        return str(self.get("post_mode") or self.settings.post_mode).lower()

    @property
    def privacy_level(self) -> str:
        return str(self.get("privacy_level") or self.settings.privacy_level)

    @property
    def caption_template(self) -> str:
        return str(self.get("caption_template") or self.settings.caption_template)

    @property
    def default_hashtags(self) -> list[str]:
        yaml_tags = self.get("default_hashtags")
        if isinstance(yaml_tags, list):
            return [str(t).strip("# ") for t in yaml_tags if str(t).strip()]
        return [t.strip() for t in self.settings.default_hashtags.split(",") if t.strip()]

    @property
    def filename_time_pattern(self) -> str | None:
        return self.get("filename_time_pattern")

    @property
    def token_path(self) -> Path:
        return self.base_dir / "data" / "tokens.json"

    @property
    def db_path(self) -> Path:
        return self.base_dir / "data" / "jobs.db"


def ensure_directories(config: AppConfig) -> None:
    config.watch_folder.mkdir(parents=True, exist_ok=True)
    config.base_dir.joinpath("data").mkdir(parents=True, exist_ok=True)
    if config.processed_folder:
        config.processed_folder.mkdir(parents=True, exist_ok=True)
    if config.failed_folder:
        config.failed_folder.mkdir(parents=True, exist_ok=True)


def load_video_metadata(video_path: Path) -> dict[str, Any]:
    meta_path = video_path.with_suffix(video_path.suffix + ".meta.json")
    if not meta_path.exists():
        meta_path = video_path.with_suffix(".json")
    if meta_path.exists():
        with meta_path.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def parse_time_from_filename(name: str, pattern: str | None) -> datetime | None:
    stem = Path(name).stem
    match = re.match(r"^(\d{8})_(\d{4})", stem)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match.group(1)}{match.group(2)}", "%Y%m%d%H%M")
    except ValueError:
        return None


def format_live_time(dt: datetime | None) -> str:
    if dt is None:
        return "近日"
    return dt.strftime("%m月%d日 %H:%M")


def build_caption(config: AppConfig, video_path: Path, metadata: dict[str, Any]) -> str:
    title = metadata.get("title") or video_path.stem
    live_time_raw = metadata.get("live_time")
    live_dt: datetime | None = None
    if live_time_raw:
        try:
            live_dt = datetime.fromisoformat(str(live_time_raw).replace("Z", "+00:00"))
        except ValueError:
            live_dt = None
    if live_dt is None:
        live_dt = parse_time_from_filename(video_path.name, config.filename_time_pattern)

    tags = metadata.get("hashtags") or config.default_hashtags
    if isinstance(tags, str):
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    else:
        tag_list = [str(t).strip() for t in tags if str(t).strip()]
    hashtags = " ".join(f"#{t.lstrip('#')}" for t in tag_list)

    template = metadata.get("caption_template") or config.caption_template
    return template.format(
        title=title,
        live_time=format_live_time(live_dt),
        hashtags=hashtags,
    ).strip()
