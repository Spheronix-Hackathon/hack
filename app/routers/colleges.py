import re

from fastapi import APIRouter, Query

from app.database.mongodb import colleges_async_collection

router = APIRouter(prefix="/api/colleges", tags=["colleges"])


@router.get("")
async def get_colleges(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=1000, ge=1, le=5000),
    include_other: bool = Query(default=True),
):
    filter_query = {"is_other": False, "name_lc": {"$ne": "other"}}
    if q and isinstance(q, str):
        escaped_q = re.escape(q.strip().lower())
        filter_query["name_lc"] = {"$regex": escaped_q, "$ne": "other"}

    projection = {"_id": 0, "name": 1, "code": 1, "sort_order": 1}
    colleges = await colleges_async_collection.find(filter_query, projection).sort("sort_order", 1).to_list(length=limit)

    return {"colleges": colleges, "total": len(colleges)}
