"""Admin API: whitelist status."""
from fastapi import APIRouter

from src.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/whitelist")
async def get_whitelist():
    """
    Show current whitelist configuration (from env).
    To change: update ZOOM_WHITELIST_MEETING_IDS and ZOOM_WHITELIST_HOST_EMAILS in .env, then restart.
    """
    return {
        "meeting_ids": settings.whitelist_meeting_ids,
        "host_emails": settings.whitelist_host_emails,
        "note": "Update .env and restart to change whitelist",
    }
