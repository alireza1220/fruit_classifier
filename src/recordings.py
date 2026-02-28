"""Recordings and meetings API — returns mock data until pipeline is implemented."""
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["recordings"])


@router.get("/recordings")
async def list_recordings(date: str | None = None, participant: str | None = None):
    """
    List recordings. Filter by date (YYYY-MM-DD) and/or participant.
    Returns mock data until audio/STT pipeline is implemented.
    """
    # Mock data for UI development
    mock_recordings = [
        {
            "id": "m1",
            "meeting_id": "9876543210",
            "title": "Q4 Planning",
            "call_date": "2025-02-28",
            "duration_minutes": 45,
            "participants": ["John Doe", "Jane Smith", "Bob Wilson"],
            "status": "completed",
        },
        {
            "id": "m2",
            "meeting_id": "12345678901",
            "title": "Sprint Review",
            "call_date": "2025-02-28",
            "duration_minutes": 30,
            "participants": ["Jane Smith", "Alice Lee"],
            "status": "completed",
        },
    ]

    if date:
        mock_recordings = [r for r in mock_recordings if r["call_date"] == date]
    if participant:
        mock_recordings = [
            r for r in mock_recordings if participant.lower() in [p.lower() for p in r["participants"]]
        ]

    return {"recordings": mock_recordings}


@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get meeting details."""
    # Mock data
    return {
        "id": meeting_id,
        "zoom_meeting_id": meeting_id,
        "title": "Q4 Planning",
        "start_time": "2025-02-28T14:00:00Z",
        "end_time": "2025-02-28T14:45:00Z",
        "call_date": "2025-02-28",
        "duration_minutes": 45,
        "host_name": "John Doe",
        "participants": ["John Doe", "Jane Smith", "Bob Wilson"],
        "status": "completed",
    }


@router.get("/meetings/{meeting_id}/summary")
async def get_summary(meeting_id: str):
    """Get meeting summary, action items, decisions."""
    return {
        "meeting_id": meeting_id,
        "summary": "The team discussed Q4 priorities and resource allocation. Key focus areas include the API migration project and the new customer onboarding flow. Budget approval was deferred to next week.",
        "action_items": [
            {"task": "Send proposal to client", "assignee": "John", "due": "2025-03-05"},
            {"task": "Review design mockups", "assignee": "Jane", "due": "2025-03-03"},
        ],
        "decisions": ["Approved Q4 budget increase", "API migration to start March 15"],
        "risks": ["Timeline may slip if design review is delayed"],
        "next_steps": ["Schedule follow-up for March 10", "Share meeting notes with stakeholders"],
    }


@router.get("/meetings/{meeting_id}/transcript")
async def get_transcript(meeting_id: str):
    """Get full transcript with timestamps."""
    return {
        "meeting_id": meeting_id,
        "segments": [
            {"speaker": "John Doe", "start_time": 0, "end_time": 5.2, "text": "Let's start with the Q4 roadmap."},
            {"speaker": "Jane Smith", "start_time": 5.5, "end_time": 12.1, "text": "I think we should prioritize the API migration. It's blocking three other projects."},
            {"speaker": "Bob Wilson", "start_time": 12.5, "end_time": 18.0, "text": "Agreed. I can have the design review done by Friday."},
        ],
    }


@router.get("/meetings/{meeting_id}/recording")
async def get_recording(meeting_id: str):
    """Get recording metadata and download URLs."""
    return {
        "meeting_id": meeting_id,
        "call_date": "2025-02-28",
        "mixed_audio_url": None,  # Presigned URL when storage is configured
        "participant_audio": {"John Doe": None, "Jane Smith": None, "Bob Wilson": None},
        "duration_seconds": 2700,
    }
