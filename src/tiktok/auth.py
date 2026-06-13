from __future__ import annotations

import json
import secrets
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from src.config import AppConfig

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
SCOPES = "user.info.basic,video.publish,video.upload"


@dataclass
class TokenData:
    access_token: str
    refresh_token: str
    open_id: str
    expires_at: datetime
    scope: str = ""

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at - timedelta(minutes=5)

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "open_id": self.open_id,
            "expires_at": self.expires_at.isoformat(),
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenData:
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            open_id=data["open_id"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            scope=data.get("scope", ""),
        )


class TikTokAuth:
    def __init__(self, config: AppConfig):
        self.config = config
        self._pending_states: dict[str, datetime] = {}

    def build_auth_url(self) -> tuple[str, str]:
        state = secrets.token_urlsafe(16)
        self._pending_states[state] = datetime.now(timezone.utc)
        params = {
            "client_key": self.config.settings.tiktok_client_key,
            "scope": SCOPES,
            "response_type": "code",
            "redirect_uri": self.config.settings.tiktok_redirect_uri,
            "state": state,
        }
        return f"{TIKTOK_AUTH_URL}?{urllib.parse.urlencode(params)}", state

    def validate_state(self, state: str) -> bool:
        created = self._pending_states.pop(state, None)
        if created is None:
            return False
        return datetime.now(timezone.utc) - created < timedelta(minutes=10)

    async def exchange_code(self, code: str) -> TokenData:
        payload = {
            "client_key": self.config.settings.tiktok_client_key,
            "client_secret": self.config.settings.tiktok_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.config.settings.tiktok_redirect_uri,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(TIKTOK_TOKEN_URL, data=payload)
            resp.raise_for_status()
            body = resp.json()
        if body.get("error", {}).get("code") not in (None, "ok"):
            raise RuntimeError(body.get("error", {}).get("message", "Token exchange failed"))
        data = body["data"]
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(data.get("expires_in", 86400)))
        token = TokenData(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            open_id=data["open_id"],
            expires_at=expires_at,
            scope=data.get("scope", ""),
        )
        self.save_token(token)
        return token

    async def refresh_token(self, token: TokenData) -> TokenData:
        payload = {
            "client_key": self.config.settings.tiktok_client_key,
            "client_secret": self.config.settings.tiktok_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(TIKTOK_TOKEN_URL, data=payload)
            resp.raise_for_status()
            body = resp.json()
        if body.get("error", {}).get("code") not in (None, "ok"):
            raise RuntimeError(body.get("error", {}).get("message", "Token refresh failed"))
        data = body["data"]
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(data.get("expires_in", 86400)))
        refreshed = TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", token.refresh_token),
            open_id=data.get("open_id", token.open_id),
            expires_at=expires_at,
            scope=data.get("scope", token.scope),
        )
        self.save_token(refreshed)
        return refreshed

    def save_token(self, token: TokenData) -> None:
        path = self.config.token_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(token.to_dict(), f, ensure_ascii=False, indent=2)

    def load_token(self) -> TokenData | None:
        path = self.config.token_path
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as f:
            return TokenData.from_dict(json.load(f))

    async def get_valid_token(self) -> TokenData | None:
        token = self.load_token()
        if token is None:
            return None
        if token.is_expired:
            token = await self.refresh_token(token)
        return token

    def is_configured(self) -> bool:
        s = self.config.settings
        return bool(s.tiktok_client_key and s.tiktok_client_secret)

    def is_authenticated(self) -> bool:
        return self.config.token_path.exists()
