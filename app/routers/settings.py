import datetime
import logging
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.database.mongodb import async_db, global_async_db, async_client

logger = logging.getLogger("app.settings")

router = APIRouter(tags=["Settings"])


def make_json_serializable(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(x) for x in obj]
    return obj


def normalize_college_list(raw_val: Any) -> List[str]:
    if not raw_val:
        return []
    if isinstance(raw_val, str):
        raw_val = raw_val.strip()
        if "\n" in raw_val:
            return [line.strip() for line in raw_val.split("\n") if line.strip()]
        if "," in raw_val and not any(raw_val.endswith(f", {dist}") for dist in ["AP", "Andhra Pradesh"]):
            # Check if it's a comma-separated list of multiple colleges or a single "College, District"
            parts = [p.strip() for p in raw_val.split(",") if p.strip()]
            if len(parts) > 2:
                return parts
        return [raw_val] if raw_val else []
    if isinstance(raw_val, list):
        items = []
        for item in raw_val:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    items.append(cleaned)
            elif isinstance(item, dict):
                name = (
                    item.get("name")
                    or item.get("college")
                    or item.get("university")
                    or item.get("collegeName")
                    or item.get("title")
                    or item.get("label")
                    or str(item)
                )
                dist = (
                    item.get("district")
                    or item.get("location")
                    or item.get("state")
                    or item.get("city")
                    or ""
                )
                items.append(f"{name}, {dist}".strip(", ") if dist else str(name).strip())
            elif item is not None:
                items.append(str(item).strip())
        return items
    return []


UNIVERSITY_KEYS = [
    "andhraBestUniversities",
    "andhraBestUniversity",
    "bestUniversities",
    "bestUniversity",
    "universityLevelColleges",
    "universityColleges",
    "andhraUniversities",
    "universities",
    "andhra_best_universities",
    "andhra_universities",
    "best_universities",
    "andhraBestColleges",
    "andhraColleges",
    "stateLevelUniversities",
]


async def extract_universities_from_db(settings_dict: dict) -> List[str]:
    # 1. Check known candidate keys in settings
    for key in UNIVERSITY_KEYS:
        if key in settings_dict and settings_dict[key]:
            parsed = normalize_college_list(settings_dict[key])
            if parsed:
                return parsed

    # 2. Check any key matching 'universit' or 'best'
    for k, val in settings_dict.items():
        if k in ["_id", "stateLevelColleges", "districtLevelColleges", "announcements", "announcement"]:
            continue
        k_lower = k.lower()
        if any(term in k_lower for term in ["universit", "bestuni", "andhrabest", "andhra_best"]):
            parsed = normalize_college_list(val)
            if parsed:
                return parsed

    # 3. Check other collections in async_db and global_async_db
    for db_ref in [async_db, global_async_db]:
        try:
            coll_names = await db_ref.list_collection_names()
            for cname in coll_names:
                c_low = cname.lower()
                if any(term in c_low for term in ["universit", "bestuni", "andhrabest", "best_college"]):
                    docs = await db_ref[cname].find({}).to_list(100)
                    extracted = []
                    for doc in docs:
                        name = (
                            doc.get("name")
                            or doc.get("university")
                            or doc.get("college")
                            or doc.get("collegeName")
                            or doc.get("title")
                        )
                        dist = doc.get("district") or doc.get("location") or doc.get("state") or ""
                        if name:
                            extracted.append(f"{name}, {dist}".strip(", ") if dist else str(name).strip())
                    if extracted:
                        return extracted
        except Exception:
            pass

    return []


@router.get("")
@router.get("/")
async def get_public_settings():
    settings_collection = async_db["settings"]
    
    # 1. Fetch exact settings document matching MongoDB screenshot (_id: 6a5602ff3a0f67c08c3d7cfc)
    doc = None
    try:
        doc = await settings_collection.find_one({"_id": ObjectId("6a5602ff3a0f67c08c3d7cfc")})
    except Exception as e:
        logger.warning(f"Error fetching document by ObjectId: {e}")

    # 2. If not found by exact ID, query latest updated document
    if not doc:
        docs = await settings_collection.find({}).sort("updatedAt", -1).to_list(100)
        for d in docs:
            if d.get("andhraBestUniversities") or d.get("stateLevelColleges"):
                doc = d
                break
        if not doc and docs:
            doc = docs[0]

    # 3. Cluster-wide scan across other databases if still not found
    if not doc:
        try:
            db_names = await async_client.list_database_names()
            for dbname in db_names:
                if dbname in ["admin", "local", "config"]:
                    continue
                db_inst = async_client[dbname]
                coll_names = await db_inst.list_collection_names()
                if "settings" in coll_names:
                    try:
                        found_doc = await db_inst["settings"].find_one({"_id": ObjectId("6a5602ff3a0f67c08c3d7cfc")})
                    except Exception:
                        found_doc = None
                    if not found_doc:
                        found_doc = await db_inst["settings"].find_one({"andhraBestUniversities": {"$exists": True}})
                    if found_doc:
                        doc = found_doc
                        settings_collection = db_inst["settings"]
                        break
        except Exception:
            pass

    if not doc:
        doc = {}

    amount = doc.get("registrationAmount", 399)
    is_open = doc.get("registrationOpen", True)
    announcement_str = ""

    if "announcements" in doc:
        val = doc["announcements"]
        if isinstance(val, list):
            announcement_str = "\n".join(str(v) for v in val if v)
        else:
            announcement_str = str(val)
    elif "announcement" in doc:
        announcement_str = str(doc["announcement"])

    # Extract all college & university lists directly from database document
    district_colleges = normalize_college_list(doc.get("districtLevelColleges", []))
    state_colleges = normalize_college_list(doc.get("stateLevelColleges", []))
    andhra_universities = normalize_college_list(
        doc.get("andhraBestUniversities") or doc.get("bestUniversities") or []
    )

    if not andhra_universities:
        andhra_universities = await extract_universities_from_db(doc)

    # 3 New Categories
    best_innovation = normalize_college_list(doc.get("bestInnovationColleges", []))
    best_emerging = normalize_college_list(doc.get("bestEmergingTechnologyColleges") or doc.get("bestEmergingTechColleges") or [])
    best_engagement = normalize_college_list(doc.get("bestStudentEngagementColleges", []))

    # Format response preserving original fields + providing standardized aliases
    res = make_json_serializable(dict(doc))
    if "_id" in res:
        res["_id"] = str(res["_id"])

    res["registrationAmount"] = amount
    res["registrationOpen"] = is_open
    res["announcement"] = announcement_str
    res["districtLevelColleges"] = district_colleges
    res["stateLevelColleges"] = state_colleges

    # Provide all alias variations so any frontend access pattern works seamlessly
    res["andhraBestUniversities"] = andhra_universities
    res["bestUniversities"] = andhra_universities
    res["universityLevelColleges"] = andhra_universities
    res["andhraUniversities"] = andhra_universities
    res["universities"] = andhra_universities
    res["andhra_best_universities"] = andhra_universities

    # 3 New Nominated College Categories
    res["bestInnovationColleges"] = best_innovation
    res["bestEmergingTechnologyColleges"] = best_emerging
    res["bestEmergingTechColleges"] = best_emerging
    res["bestStudentEngagementColleges"] = best_engagement

    # Hero Banner flip images
    try:
        from app.routers.flip_images import get_current_flip_images
        res["flipImages"] = await get_current_flip_images()
    except Exception as e:
        logger.warning(f"Could not load flip images: {e}")
        res["flipImages"] = []

    return JSONResponse(
        content=res,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )


@router.post("")
@router.post("/")
@router.post("/update")
@router.put("")
@router.put("/")
@router.put("/update")
@router.patch("")
@router.patch("/")
@router.patch("/update")
async def update_settings(request: Request):
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as e:
        logger.warning(f"Could not parse request body as JSON: {e}")
        body = {}

    settings_collection = async_db["settings"]
    update_data: Dict[str, Any] = {}

    # 1. Standard settings fields
    if "registrationAmount" in body and body["registrationAmount"] is not None:
        try:
            update_data["registrationAmount"] = float(body["registrationAmount"])
        except (ValueError, TypeError):
            update_data["registrationAmount"] = body["registrationAmount"]

    if "registrationOpen" in body and body["registrationOpen"] is not None:
        update_data["registrationOpen"] = bool(body["registrationOpen"])

    if "announcements" in body and body["announcements"] is not None:
        update_data["announcements"] = body["announcements"]
    if "announcement" in body and body["announcement"] is not None:
        update_data["announcement"] = str(body["announcement"])

    # 2. State Level Colleges
    if "stateLevelColleges" in body and body["stateLevelColleges"] is not None:
        update_data["stateLevelColleges"] = normalize_college_list(body["stateLevelColleges"])

    # 3. District Level Colleges
    if "districtLevelColleges" in body and body["districtLevelColleges"] is not None:
        update_data["districtLevelColleges"] = normalize_college_list(body["districtLevelColleges"])

    # 4. University list candidates
    found_unis = None
    for key in UNIVERSITY_KEYS:
        if key in body and body[key] is not None:
            found_unis = normalize_college_list(body[key])
            break

    # If single item addition e.g. { "college": "kvsrit", "type": "university" }
    if found_unis is None:
        single_college = body.get("college") or body.get("collegeName") or body.get("university") or body.get("name")
        item_type = str(body.get("type") or body.get("category") or body.get("level") or "").lower()
        if single_college:
            cleaned_single = str(single_college).strip()
            if any(term in item_type for term in ["universit", "best", "andhra"]):
                # Append to existing universities
                current_doc = await settings_collection.find_one({}) or {}
                existing_unis = normalize_college_list(
                    current_doc.get("andhraBestUniversities") or current_doc.get("bestUniversities") or []
                )
                if cleaned_single not in existing_unis:
                    existing_unis.append(cleaned_single)
                found_unis = existing_unis
            elif "state" in item_type:
                current_doc = await settings_collection.find_one({}) or {}
                existing_states = normalize_college_list(current_doc.get("stateLevelColleges") or [])
                if cleaned_single not in existing_states:
                    existing_states.append(cleaned_single)
                update_data["stateLevelColleges"] = existing_states
            elif "district" in item_type:
                current_doc = await settings_collection.find_one({}) or {}
                existing_dists = normalize_college_list(current_doc.get("districtLevelColleges") or [])
                if cleaned_single not in existing_dists:
                    existing_dists.append(cleaned_single)
                update_data["districtLevelColleges"] = existing_dists

    if found_unis is not None:
        update_data["andhraBestUniversities"] = found_unis
        update_data["bestUniversities"] = found_unis
        update_data["universityLevelColleges"] = found_unis
        update_data["andhraUniversities"] = found_unis
        update_data["universities"] = found_unis
        update_data["andhra_best_universities"] = found_unis

    # 5. Best Innovation Colleges
    if "bestInnovationColleges" in body and body["bestInnovationColleges"] is not None:
        update_data["bestInnovationColleges"] = normalize_college_list(body["bestInnovationColleges"])

    # 6. Best Emerging Technology Colleges
    if ("bestEmergingTechnologyColleges" in body and body["bestEmergingTechnologyColleges"] is not None) or ("bestEmergingTechColleges" in body and body["bestEmergingTechColleges"] is not None):
        val = body.get("bestEmergingTechnologyColleges") or body.get("bestEmergingTechColleges")
        update_data["bestEmergingTechnologyColleges"] = normalize_college_list(val)
        update_data["bestEmergingTechColleges"] = normalize_college_list(val)

    # 7. Best Student Engagement Colleges
    if "bestStudentEngagementColleges" in body and body["bestStudentEngagementColleges"] is not None:
        update_data["bestStudentEngagementColleges"] = normalize_college_list(body["bestStudentEngagementColleges"])

    # 5. Preserve any extra keys passed by admin
    for k, v in body.items():
        if k not in update_data and k != "_id":
            update_data[k] = v

    if update_data:
        await settings_collection.update_one({}, {"$set": update_data}, upsert=True)
        logger.info(f"Updated settings with keys: {list(update_data.keys())}")

    return {
        "success": True,
        "message": "Settings updated successfully",
        "updated": update_data,
    }


@router.get("/debug")
async def debug_settings():
    docs = await async_db["settings"].find({}).to_list(100)
    colls = await async_db.list_collection_names()
    global_colls = []
    try:
        global_colls = await global_async_db.list_collection_names()
    except Exception:
        pass
    return JSONResponse(
        content=make_json_serializable({
            "database_name": async_db.name,
            "collections": colls,
            "global_database_name": global_async_db.name,
            "global_collections": global_colls,
            "settings_docs": docs,
        })
    )
