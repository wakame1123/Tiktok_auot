from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from src.config import AppConfig
from src.tiktok.auth import TikTokAuth, TokenData

CHUNK_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass
class PublishResult:
    publish_id: str
    status: str
    fail_reason: str = ""
    post_id: str = ""


class TikTokClient:
    BASE = "https://open.tiktokapis.com"

    def __init__(self, config: AppConfig, auth: TikTokAuth):
        self.config = config
        self.auth = auth

    async def _headers(self, token: TokenData) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    async def query_creator_info(self, token: TokenData) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE}/v2/post/publish/creator_info/query/",
                headers=await self._headers(token),
                json={},
            )
            resp.raise_for_status()
            body = resp.json()
        err = body.get("error", {})
        if err.get("code") not in (None, "ok"):
            raise RuntimeError(err.get("message", "creator_info query failed"))
        return body["data"]

    async def publish_video_direct(
        self,
        token: TokenData,
        video_path: Path,
        caption: str,
        privacy_level: str | None = None,
    ) -> PublishResult:
        creator = await self.query_creator_info(token)
        allowed = creator.get("privacy_level_options", [])
        privacy = privacy_level or self.config.privacy_level
        if privacy not in allowed:
            privacy = allowed[0] if allowed else "SELF_ONLY"

        video_size = video_path.stat().st_size
        chunk_count = max(1, math.ceil(video_size / CHUNK_SIZE))
        chunk_size = min(CHUNK_SIZE, video_size)

        init_body = {
            "post_info": {
                "title": caption[:2200],
                "privacy_level": privacy,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": chunk_count,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.BASE}/v2/post/publish/video/init/",
                headers=await self._headers(token),
                json=init_body,
            )
            resp.raise_for_status()
            init_data = resp.json()
            err = init_data.get("error", {})
            if err.get("code") not in (None, "ok"):
                raise RuntimeError(err.get("message", "video init failed"))

            publish_id = init_data["data"]["publish_id"]
            upload_url = init_data["data"]["upload_url"]

            with video_path.open("rb") as f:
                data = f.read()

            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(data)),
                "Content-Range": f"bytes 0-{len(data) - 1}/{len(data)}",
            }
            upload_resp = await client.put(upload_url, headers=upload_headers, content=data)
            upload_resp.raise_for_status()

        return await self.wait_for_publish(token, publish_id)

    async def publish_video_draft(
        self,
        token: TokenData,
        video_path: Path,
        caption: str,
    ) -> PublishResult:
        """TikTok受信箱に下書きとしてアップロード（LIVEステッカー追加はアプリ側で）"""
        video_size = video_path.stat().st_size
        chunk_count = max(1, math.ceil(video_size / CHUNK_SIZE))
        chunk_size = min(CHUNK_SIZE, video_size)

        init_body = {
            "post_info": {
                "title": caption[:2200],
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": chunk_count,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.BASE}/v2/post/publish/inbox/video/init/",
                headers=await self._headers(token),
                json=init_body,
            )
            resp.raise_for_status()
            init_data = resp.json()
            err = init_data.get("error", {})
            if err.get("code") not in (None, "ok"):
                raise RuntimeError(err.get("message", "draft init failed"))

            publish_id = init_data["data"]["publish_id"]
            upload_url = init_data["data"]["upload_url"]

            with video_path.open("rb") as f:
                data = f.read()

            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(data)),
                "Content-Range": f"bytes 0-{len(data) - 1}/{len(data)}",
            }
            upload_resp = await client.put(upload_url, headers=upload_headers, content=data)
            upload_resp.raise_for_status()

        return PublishResult(publish_id=publish_id, status="SENT_TO_USER_INBOX")

    async def wait_for_publish(
        self,
        token: TokenData,
        publish_id: str,
        max_attempts: int = 30,
        interval: float = 2.0,
    ) -> PublishResult:
        for _ in range(max_attempts):
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.BASE}/v2/post/publish/status/fetch/",
                    headers=await self._headers(token),
                    json={"publish_id": publish_id},
                )
                resp.raise_for_status()
                body = resp.json()
            err = body.get("error", {})
            if err.get("code") not in (None, "ok"):
                raise RuntimeError(err.get("message", "status fetch failed"))

            data = body["data"]
            status = data.get("status", "PROCESSING")
            if status in ("PUBLISH_COMPLETE", "FAILED"):
                return PublishResult(
                    publish_id=publish_id,
                    status=status,
                    fail_reason=data.get("fail_reason", ""),
                    post_id=str(data.get("publicaly_available_post_id", "")),
                )
            await asyncio.sleep(interval)

        return PublishResult(publish_id=publish_id, status="TIMEOUT")

    async def publish(
        self,
        video_path: Path,
        caption: str,
        privacy_level: str | None = None,
    ) -> PublishResult:
        token = await self.auth.get_valid_token()
        if token is None:
            raise RuntimeError("TikTok未認証です。Web UIからログインしてください。")

        if self.config.post_mode == "draft":
            return await self.publish_video_draft(token, video_path, caption)
        return await self.publish_video_direct(token, video_path, caption, privacy_level)
