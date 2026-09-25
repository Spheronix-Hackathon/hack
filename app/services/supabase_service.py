import base64
import logging
from typing import Optional

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BUCKET_NAME = "students-payment-receipts"

# Try importing official supabase client
try:
    from supabase import Client, create_client
    HAS_SUPABASE_SDK = True
except ImportError:
    Client = None
    create_client = None
    HAS_SUPABASE_SDK = False


def get_supabase_client():
    if not HAS_SUPABASE_SDK:
        return None
    if not settings.supabase_url or not settings.supabase_anon_key:
        logger.warning("Supabase configuration missing (SUPABASE_URL or SUPABASE_ANON_KEY).")
        return None
    try:
        return create_client(settings.supabase_url, settings.supabase_anon_key)
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}")
        return None


def get_content_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    elif lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    elif lower.endswith(".pdf"):
        return "application/pdf"
    elif lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


async def upload_receipt_to_supabase(base64_data: str, filename: str) -> Optional[str]:
    """
    Decodes the base64 receipt data, uploads it to Supabase Storage in the
    'students-payment-receipts' bucket, and returns the public URL.
    """
    if not base64_data or not filename:
        return None

    supabase_url = (settings.supabase_url or "").rstrip("/")
    supabase_key = settings.supabase_anon_key
    if not supabase_url or not supabase_key:
        logger.warning("Supabase URL or Anon Key not configured in settings.")
        return None

    try:
        # Remove data URI scheme prefix if present
        if "base64," in base64_data:
            base64_data = base64_data.split("base64,")[1]

        file_bytes = base64.b64decode(base64_data)
        content_type = get_content_type(filename)

        # 1. Attempt using official Supabase client if available
        client = get_supabase_client()
        if client:
            try:
                bucket = client.storage.from_(BUCKET_NAME)
                bucket.upload(
                    path=filename,
                    file=file_bytes,
                    file_options={
                        "content-type": content_type,
                        "upsert": "true",
                    },
                )
                public_url = bucket.get_public_url(filename)
                logger.info(f"Successfully uploaded receipt to Supabase via SDK: {public_url}")
                return public_url
            except Exception as sdk_err:
                logger.warning(f"Supabase SDK upload failed, attempting REST API fallback: {sdk_err}")

        # 2. Resilient REST API fallback via httpx
        storage_url = f"{supabase_url}/storage/v1/object/{BUCKET_NAME}/{filename}"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            res = await http_client.post(storage_url, content=file_bytes, headers=headers)
            if res.status_code in [200, 201]:
                public_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
                logger.info(f"Successfully uploaded receipt to Supabase via REST: {public_url}")
                return public_url
            else:
                logger.error(
                    f"Supabase REST upload failed with status {res.status_code}: {res.text}"
                )
                return None

    except Exception as e:
        logger.error(f"Failed to upload receipt {filename} to Supabase: {e}")
        return None
