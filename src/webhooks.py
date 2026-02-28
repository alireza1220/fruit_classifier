"""Zoom webhook handler."""
import hashlib
import hmac
import logging
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse

from src.config import settings
from src.whitelist import is_whitelisted
from src.zoom import verify_webhook_signature, get_access_token, get_meeting, get_join_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/zoom")
async def zoom_webhook(request: Request) -> Response:
    """
    Receive Zoom webhooks. Validates signature, checks whitelist, triggers bot join.
    """
    body = await request.body()
    signature = request.headers.get("x-zm-signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    data = await request.json()
    event = data.get("event")
    payload = data.get("payload", {})

    # Zoom sends validation challenge on webhook setup
    if event == "endpoint.url_validation":
        return _handle_validation(data)

    if event == "meeting.started":
        await _handle_meeting_started(payload)
    elif event == "meeting.ended":
        await _handle_meeting_ended(payload)
    elif event in ("meeting.participant_joined", "meeting.participant_left"):
        await _handle_participant_event(event, payload)

    return Response(status_code=200)


def _handle_validation(data: dict) -> Response:
    """Respond to Zoom webhook URL validation challenge."""
    plain_token = data.get("payload", {}).get("plainToken", "")
    encrypted = hmac.new(
        settings.zoom_webhook_secret_token.encode(),
        plain_token.encode(),
        hashlib.sha256,
    ).hexdigest()
    return JSONResponse(content={"plainToken": plain_token, "encryptedToken": encrypted})


async def _handle_meeting_started(payload: dict) -> None:
    """On meeting start: check whitelist, get join token, trigger bot join."""
    obj = payload.get("object", {})
    meeting_id = str(obj.get("id", ""))
    host_id = str(obj.get("host_id", "")) if obj.get("host_id") else ""
    host_email = (obj.get("host_email") or "").lower()

    # Fetch meeting details for host info (needed for whitelist + join)
    try:
        token = await get_access_token()
        meeting = await get_meeting(meeting_id, token)
        host_id = host_id or str(meeting.get("host_id", ""))
        host_email = host_email or (meeting.get("host_email") or "").lower()
    except Exception as e:
        logger.warning("Could not fetch meeting %s: %s", meeting_id, e)
        return

    if not is_whitelisted(meeting_id=meeting_id, host_email=host_email, host_id=host_id):
        logger.info("Meeting %s not whitelisted, skipping join", meeting_id)
        return

    logger.info("Meeting %s whitelisted, preparing bot join", meeting_id)

    try:
        join_data = await get_join_token(meeting_id, token)
        logger.info(
            "Join token obtained for meeting %s. Use Zoom Meeting SDK for Linux to join. "
            "Join URL: %s",
            meeting_id,
            meeting.get("join_url", "N/A"),
        )
        # TODO: Emit to Redis/bot-service to trigger SDK container join
        _ = join_data  # join_data contains token for SDK
    except Exception as e:
        logger.exception("Failed to get join token for meeting %s: %s", meeting_id, e)


async def _handle_meeting_ended(payload: dict) -> None:
    """On meeting end: finalize recording, trigger STT pipeline."""
    obj = payload.get("object", {})
    meeting_id = str(obj.get("id", ""))
    logger.info("Meeting %s ended", meeting_id)
    # TODO: Signal audio service to finalize, trigger STT


async def _handle_participant_event(event: str, payload: dict) -> None:
    """Track participant join/leave."""
    obj = payload.get("object", {})
    meeting_id = str(obj.get("id", ""))
    participant = obj.get("participant", {})
    logger.debug("%s: meeting=%s participant=%s", event, meeting_id, participant.get("user_name"))
