from fastapi import APIRouter, Response
from app.services.settings_service import get_payment_settings

router = APIRouter(prefix="/api/public-settings", tags=["Settings"])

@router.get("")
@router.get("/")
async def get_public_settings(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return await get_payment_settings()
