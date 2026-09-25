from fastapi import APIRouter
from app.database.mongodb import global_data_async_collection, branches_async_collection

router = APIRouter(prefix="/api", tags=["tasks"])

@router.get("/task-categories")
async def get_task_categories():
    projection = {"_id": 0, "name": 1}
    categories = await global_data_async_collection.find({}, projection).to_list(length=100)
    
    seen = set()
    category_list = []
    
    def get_canonical(name_str: str) -> tuple[str, str]:
        low = name_str.lower()
        if "full stack" in low or "fullstack" in low:
            return ("fullstack", "Full Stack Application")
        if "bug" in low:
            return ("bughunt", "Bug Hunt")
        if "native" in low or "windows" in low:
            return ("nativeapps", "Native Apps (Windows)")
        if "ideathon" in low:
            return ("ideathon", "Ideathon")
        return (low, name_str)

    for c in categories:
        raw_name = (c.get("name") or "").strip()
        if not raw_name:
            continue
        key, display_name = get_canonical(raw_name)
        if key not in seen:
            seen.add(key)
            category_list.append(display_name)
            
    defaults = [
        ("fullstack", "Full Stack Application"),
        ("bughunt", "Bug Hunt"),
        ("nativeapps", "Native Apps (Windows)"),
        ("ideathon", "Ideathon"),
        ("other", "Other"),
    ]
    for key, display_name in defaults:
        if key not in seen:
            seen.add(key)
            category_list.append(display_name)
            
    return category_list

@router.get("/branches")
async def get_branches():
    projection = {"_id": 0, "name": 1}
    branches = await branches_async_collection.find({}, projection).sort("name", 1).to_list(length=100)
    branch_names = [b["name"] for b in branches if b.get("name") and b["name"].strip().lower() != "other"]
    branch_names.append("Other")
    return branch_names
