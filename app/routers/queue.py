from fastapi import APIRouter, Cookie, Query, Response
from typing import Optional

from app.core.waiting_room import waiting_room
from config.settings import get_settings

router = APIRouter(prefix="/api/queue", tags=["Queue / Waiting Room"])
settings = get_settings()


@router.get("/request")
async def request_queue_entry(
    response: Response,
    ticket: Optional[str] = Query(None),
    queue_pass: Optional[str] = Cookie(None),
):
    """
    Request entry to registration.
    If admitted, sets 'queue_pass' cookie and returns admitted status.
    If busy, returns queue ticket and position for waiting room.
    """
    # 1. Already has valid pass?
    if queue_pass and waiting_room.verify_token(queue_pass):
        return {"status": "admitted", "admitted": True, "token": queue_pass}

    # 2. Request entry or join queue
    result = await waiting_room.request_entry(ticket)

    if result.get("admitted") and result.get("token"):
        response.set_cookie(
            key="queue_pass",
            value=result["token"],
            max_age=settings.queue_pass_ttl,
            httponly=False,  # Allow frontend to verify pass
            samesite="lax",
            secure=settings.is_production,
        )

    return result


@router.get("/status")
async def get_queue_status(
    response: Response,
    ticket: str = Query(...),
):
    """
    Poll queue status while waiting in the virtual waiting room.
    """
    result = await waiting_room.get_ticket_status(ticket)

    if result.get("admitted") and result.get("token"):
        response.set_cookie(
            key="queue_pass",
            value=result["token"],
            max_age=settings.queue_pass_ttl,
            httponly=False,
            samesite="lax",
            secure=settings.is_production,
        )

    return result


@router.get("/stats")
async def get_queue_stats():
    """
    Queue telemetry: total waiting, rate of admission.
    """
    return {
        "queue_enabled": settings.queue_enabled,
        "admit_rate_per_sec": settings.queue_admit_rate,
        "max_active": settings.queue_max_active,
        "waiting_in_line": len(waiting_room._queue),
        "currently_admitted_active": len(waiting_room._admitted),
    }
