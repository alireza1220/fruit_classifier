"""Whitelist logic: determines if the bot should join a meeting."""
from src.config import settings


def is_whitelisted(
    meeting_id: str | None = None,
    host_email: str | None = None,
    host_id: str | None = None,
) -> bool:
    """
    Check if a meeting is whitelisted for the bot to join.

    Returns True if:
    - meeting_id is in ZOOM_WHITELIST_MEETING_IDS, or
    - host_email is in ZOOM_WHITELIST_HOST_EMAILS

    Returns False if no whitelist entries exist (bot joins nothing).
    """
    meeting_ids = settings.whitelist_meeting_ids
    host_emails = settings.whitelist_host_emails

    # Empty whitelist = join nothing
    if not meeting_ids and not host_emails:
        return False

    if meeting_id and meeting_id in meeting_ids:
        return True

    if host_email and host_email.lower() in host_emails:
        return True

    return False
