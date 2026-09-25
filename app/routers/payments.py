import base64
import logging
import os
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.core.rate_limit import limiter
from app.core.time_utils import utc_now
from app.database.mongodb import registrations_async_collection
from app.models.schemas import PaymentOrderRequest, PaymentVerification
from app.services.payment_service import create_order, verify_upi_payment
from config.settings import get_settings

router = APIRouter(prefix="/api/payment", tags=["payments"])
settings = get_settings()
logger = logging.getLogger(__name__)

RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads", "receipts")
os.makedirs(RECEIPTS_DIR, exist_ok=True)
MAX_RECEIPT_BYTES = 100 * 1024  # 100 KB
ALLOWED_RECEIPT_EXTENSIONS = {".png", ".jpg", ".jpeg"}


@router.post("/order")
@limiter.limit("60/minute")
async def create_payment_order(request: Request, payload: PaymentOrderRequest):
    return await create_order(payload)


@router.post("/verify")
@limiter.limit("60/minute")
async def verify_payment(request: Request, data: PaymentVerification):
    try:
        order_id = data.effective_order_id
        transaction_id = data.effective_transaction_id

        if not order_id:
            raise HTTPException(status_code=400, detail="Order ID is required for verification.")

        # Check if already paid to support recovery
        existing_doc = await registrations_async_collection.find_one(
            {"rzp_order_id": order_id},
            {"payment.status": 1, "payment.transaction_id": 1},
        )
        if existing_doc and str(existing_doc.get("payment", {}).get("status") or "").lower() in ["success", "paid", "captured"]:
            final_payment_id = existing_doc.get("payment", {}).get("transaction_id") or transaction_id or "UPI_PAID"
            return {
                "status": "success",
                "message": "Payment already verified.",
                "order_id": order_id,
                "transaction_id": final_payment_id,
                "rzp_order_id": order_id,
                "rzp_payment_id": final_payment_id,
            }

        verified_payment = await verify_upi_payment(order_id, transaction_id)
        return verified_payment

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Payment verification error")
        raise HTTPException(status_code=500, detail=f"Payment verification error: {exc}")


@router.post("/verify-upi")
@limiter.limit("10/minute")
async def verify_upi(request: Request, data: PaymentVerification):
    return await verify_payment(request, data)


# ============ Payment Receipt / Screenshot Upload (Max 100KB) ============
@router.post("/upload-receipt")
@limiter.limit("15/minute")
async def upload_payment_receipt(request: Request, file: UploadFile = File(...)):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file selected for upload.")

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_RECEIPT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed formats: PNG, JPG, JPEG.",
        )

    # Read content and enforce 100KB limit
    content = await file.read()
    if len(content) > MAX_RECEIPT_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds maximum allowed limit of 100KB.",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Validate file magic bytes to prevent masqueraded files
    is_valid_signature = False
    if ext == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"):
        is_valid_signature = True
    elif ext in [".jpg", ".jpeg"] and content.startswith(b"\xff\xd8\xff"):
        is_valid_signature = True

    if not is_valid_signature:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file content does not match genuine {ext.upper().lstrip('.')} format.",
        )

    # Generate Base64 Data URI
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    mime_type = mime_types.get(ext, "image/png")
    encoded_b64 = base64.b64encode(content).decode("utf-8")
    base64_data_uri = f"data:{mime_type};base64,{encoded_b64}"

    # Sanitize original filename and generate unique stored filename
    safe_basename = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:8]
    stored_filename = f"{timestamp}_{unique_suffix}_{safe_basename}"

    full_url = None
    file_url = None

    # 1. Attempt upload to Supabase Storage first
    try:
        from app.services.supabase_service import upload_receipt_to_supabase
        supabase_url = await upload_receipt_to_supabase(base64_data_uri, stored_filename)
        if supabase_url:
            full_url = supabase_url
            file_url = supabase_url  # Not local, but satisfies client expectations
            logger.info("[SUPABASE UPLOAD SUCCESS] Uploaded receipt to Supabase: %s", full_url)
    except Exception as sup_err:
        logger.warning("Supabase upload in /upload-receipt skipped/failed: %s", sup_err)

    # 2. Fallback to Local Disk if Supabase failed or isn't configured
    if not full_url:
        file_path = os.path.join(RECEIPTS_DIR, stored_filename)
        with open(file_path, "wb") as f:
            f.write(content)

        file_url = f"/uploads/receipts/{stored_filename}"
        current_settings = get_settings()
        base_url = (current_settings.app_base_url or "https://puhackathon.spheronixtechnology.com").rstrip("/")
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[7:]
        elif not base_url.startswith("https://"):
            base_url = f"https://{base_url}"

        full_url = f"{base_url}{file_url}"
        
        logger.info(
            "[RECEIPT UPLOAD SUCCESS] Saved receipt file '%s' (%d bytes) locally to '%s' | URL: %s",
            file.filename,
            len(content),
            file_path,
            full_url,
        )

    return {
        "status": "success",
        "fileUrl": full_url,
        "fullUrl": full_url,
        "base64": base64_data_uri,
        "payment_receipt_base64": base64_data_uri,
        "receipt_base64": base64_data_uri,
        "relativeUrl": file_url,
        "filename": stored_filename,
        "originalName": file.filename,
        "sizeBytes": len(content),
    }


@router.get("/receipt/{filename}")
@router.get("/view-receipt/{filename}")
async def view_uploaded_receipt(filename: str):
    clean_filename = os.path.basename(filename)
    file_path = os.path.join(RECEIPTS_DIR, clean_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Receipt file not found on server.")

    ext = os.path.splitext(clean_filename)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{clean_filename}"',
            "Cache-Control": "public, max-age=86400",
        },
    )
