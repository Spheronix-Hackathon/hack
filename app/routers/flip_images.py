import os
import uuid
import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.database.mongodb import async_db, settings_collection
from app.services.auth_service import AuthService

logger = logging.getLogger("app.flip_images")

router = APIRouter(prefix="/api", tags=["Flip Images"])

STATIC_FLIP_DIR = os.path.join("static", "images", "flip")
os.makedirs(STATIC_FLIP_DIR, exist_ok=True)

DEFAULT_FLIP_IMAGES: List[Dict[str, Any]] = [
    {"id": "flip-1", "url": "images/flip/1.jpeg", "title": "Hackathon Brainstorming", "type": "default"},
    {"id": "flip-2", "url": "images/flip/2.jpeg", "title": "Team Coding Session", "type": "default"},
    {"id": "flip-3", "url": "images/flip/3.jpeg", "title": "Collaboration Discussion", "type": "default"},
    {"id": "flip-4", "url": "images/flip/4.jpeg", "title": "Project Development", "type": "default"},
    {"id": "flip-5", "url": "images/flip/5.jpeg", "title": "Tech Hackathon Sprint", "type": "default"},
    {"id": "flip-6", "url": "images/flip/6.jpeg", "title": "Mentorship & Guidance", "type": "default"},
]

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}


import base64

async def get_current_flip_images() -> List[Dict[str, Any]]:
    """Retrieve the current flip images list from the database, or return defaults."""
    doc = await settings_collection.find_one({})
    if doc and "flipImages" in doc and isinstance(doc["flipImages"], list) and len(doc["flipImages"]) > 0:
        cleaned = []
        for idx, item in enumerate(doc["flipImages"]):
            if isinstance(item, str):
                cleaned.append({
                    "id": f"img-{idx+1}",
                    "url": item,
                    "title": f"Image {idx+1}",
                    "type": "link",
                })
            elif isinstance(item, dict):
                # Auto-sync dataUrl to disk if file does not exist on disk yet
                url = item.get("url", "")
                data_url = item.get("dataUrl", "")
                if url.startswith("images/flip/") and data_url and "," in data_url:
                    filename = os.path.basename(url)
                    disk_path = os.path.join(STATIC_FLIP_DIR, filename)
                    if not os.path.exists(disk_path):
                        try:
                            encoded = data_url.split(",", 1)[1]
                            with open(disk_path, "wb") as f:
                                f.write(base64.b64decode(encoded))
                            logger.info(f"Auto-synced dataUrl to local file: {disk_path}")
                        except Exception as e:
                            logger.warning(f"Failed to auto-sync dataUrl for {url}: {e}")
                cleaned.append(item)
        return cleaned
    return list(DEFAULT_FLIP_IMAGES)


async def verify_admin_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify admin JWT token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    token = authorization.split(" ")[1]
    payload = AuthService.decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user_id = payload.get("userId")
    user = await AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    return user


class LinkImageRequest(BaseModel):
    url: str
    title: Optional[str] = None


class DeleteImageRequest(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None


class ReorderRequest(BaseModel):
    imageIds: List[str]


# ── PUBLIC ENDPOINTS ─────────────────────────────────────────────────────────

@router.get("/flip-images")
@router.get("/public/flip-images")
async def list_flip_images():
    """Public endpoint to fetch flip images for the landing page hero carousel."""
    images = await get_current_flip_images()
    return JSONResponse(
        content={
            "success": True,
            "images": images,
            "count": len(images),
        },
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# ── ADMIN ENDPOINTS ──────────────────────────────────────────────────────────

@router.get("/admin/flip-images")
async def admin_list_flip_images(user: Dict[str, Any] = None):
    """Admin endpoint to view all flip images with full details."""
    images = await get_current_flip_images()
    return {
        "success": True,
        "images": images,
        "count": len(images),
    }


@router.post("/admin/flip-images/upload")
async def admin_upload_flip_image(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
):
    """Admin uploads a new image file to static/images/flip/ and registers it in the DB."""
    await verify_admin_token(authorization)

    filename = file.filename or "upload.jpg"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read and validate content size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    # Generate safe unique filename
    unique_suffix = f"{int(datetime.datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    clean_base = "".join(c for c in os.path.splitext(filename)[0] if c.isalnum() or c in ("-", "_"))[:30] or "flip"
    safe_filename = f"{clean_base}_{unique_suffix}{ext}"
    dest_path = os.path.join(STATIC_FLIP_DIR, safe_filename)

    with open(dest_path, "wb") as f:
        f.write(content)

    new_img: Dict[str, Any] = {
        "id": f"flip-{uuid.uuid4().hex[:8]}",
        "url": f"images/flip/{safe_filename}",
        "title": (title or os.path.splitext(filename)[0]).strip(),
        "type": "upload",
        "filename": safe_filename,
        "sizeBytes": len(content),
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    current_images = await get_current_flip_images()
    current_images.append(new_img)

    await settings_collection.update_one(
        {},
        {"$set": {"flipImages": current_images, "updatedAt": datetime.datetime.now(datetime.timezone.utc)}},
        upsert=True,
    )
    logger.info(f"Admin uploaded flip image: {safe_filename}")

    return {
        "success": True,
        "message": "Image uploaded successfully!",
        "image": new_img,
        "images": current_images,
    }


@router.post("/admin/flip-images/link")
async def admin_add_flip_image_link(
    req: LinkImageRequest,
    authorization: Optional[str] = Header(None),
):
    """Admin adds an image URL (formatted link) to the flip images."""
    await verify_admin_token(authorization)

    url = (req.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="Image URL cannot be empty.")

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("images/") or url.startswith("/images/")):
        raise HTTPException(status_code=400, detail="Invalid image URL. Must start with http://, https://, or images/")

    new_img: Dict[str, Any] = {
        "id": f"flip-{uuid.uuid4().hex[:8]}",
        "url": url,
        "title": (req.title or "External Flip Image").strip(),
        "type": "link",
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    current_images = await get_current_flip_images()
    current_images.append(new_img)

    await settings_collection.update_one(
        {},
        {"$set": {"flipImages": current_images, "updatedAt": datetime.datetime.now(datetime.timezone.utc)}},
        upsert=True,
    )
    logger.info(f"Admin added flip image link: {url}")

    return {
        "success": True,
        "message": "Image link added successfully!",
        "image": new_img,
        "images": current_images,
    }


@router.post("/admin/flip-images/delete")
@router.delete("/admin/flip-images/{image_id}")
async def admin_delete_flip_image(
    image_id: Optional[str] = None,
    req: Optional[DeleteImageRequest] = None,
    authorization: Optional[str] = Header(None),
):
    """Admin deletes a flip image by ID or URL. If uploaded file, cleans up disk."""
    await verify_admin_token(authorization)

    target_id = image_id or (req.id if req else None)
    target_url = req.url if req else None

    current_images = await get_current_flip_images()
    removed_item = None
    remaining = []

    for img in current_images:
        matches_id = target_id and img.get("id") == target_id
        matches_url = target_url and (img.get("url") == target_url or img.get("url") == target_url.lstrip("/"))
        if matches_id or matches_url:
            removed_item = img
        else:
            remaining.append(img)

    if not removed_item:
        raise HTTPException(status_code=404, detail="Image not found in flip collection.")

    # Clean up file on disk if it was an uploaded file (and not the original 1..6.jpeg default)
    filename = removed_item.get("filename")
    if filename:
        file_path = os.path.join(STATIC_FLIP_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted flip image file from disk: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete file {file_path}: {e}")

    await settings_collection.update_one(
        {},
        {"$set": {"flipImages": remaining, "updatedAt": datetime.datetime.now(datetime.timezone.utc)}},
        upsert=True,
    )

    return {
        "success": True,
        "message": f"Deleted image '{removed_item.get('title', 'Image')}' successfully.",
        "images": remaining,
    }


@router.post("/admin/flip-images/reorder")
async def admin_reorder_flip_images(
    req: ReorderRequest,
    authorization: Optional[str] = Header(None),
):
    """Admin changes the display order of flip images."""
    await verify_admin_token(authorization)

    current_images = await get_current_flip_images()
    img_by_id = {img.get("id"): img for img in current_images}

    reordered = []
    for img_id in req.imageIds:
        if img_id in img_by_id:
            reordered.append(img_by_id[img_id])

    # Append any remaining images that weren't in the provided list
    seen_ids = set(req.imageIds)
    for img in current_images:
        if img.get("id") not in seen_ids:
            reordered.append(img)

    await settings_collection.update_one(
        {},
        {"$set": {"flipImages": reordered, "updatedAt": datetime.datetime.now(datetime.timezone.utc)}},
        upsert=True,
    )

    return {
        "success": True,
        "message": "Flip images reordered successfully.",
        "images": reordered,
    }


@router.post("/admin/flip-images/reset-defaults")
async def admin_reset_default_flip_images(authorization: Optional[str] = Header(None)):
    """Admin resets the flip images back to the default 6 event photos."""
    await verify_admin_token(authorization)

    await settings_collection.update_one(
        {},
        {"$set": {"flipImages": list(DEFAULT_FLIP_IMAGES), "updatedAt": datetime.datetime.now(datetime.timezone.utc)}},
        upsert=True,
    )

    return {
        "success": True,
        "message": "Reset to default flip images successfully.",
        "images": DEFAULT_FLIP_IMAGES,
    }
