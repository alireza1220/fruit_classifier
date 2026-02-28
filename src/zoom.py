"""Zoom API client: OAuth tokens, meeting details, join tokens."""
import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx
from src.config import settings


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Zoom webhook signature using ZOOM_WEBHOOK_SECRET_TOKEN."""
    if not settings.zoom_webhook_secret_token:
        return False
    message = f"v0:{payload.decode()}"
    expected = "v0=" + hmac.new(
        settings.zoom_webhook_secret_token.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def get_access_token() -> str:
    """Get Server-to-Server OAuth access token."""
    credentials = base64.b64encode(
        f"{settings.zoom_client_id}:{settings.zoom_client_secret}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://zoom.us/oauth/token",
            params={"grant_type": "account_credentials", "account_id": settings.zoom_account_id},
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        r.raise_for_status()
        return r.json()["access_token"]


async def get_meeting(meeting_id: str, token: str) -> dict:
    """Get meeting details including passcode if required."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://api.zoom.us/v2/meetings/{meeting_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()


async def get_join_token(meeting_id: str, token: str) -> dict:
    """
    Get join token for local recording (bot join).
    Required for Meeting SDK to join as a bot.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://api.zoom.us/v2/meetings/{meeting_id}/jointoken/local_recording",
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()
