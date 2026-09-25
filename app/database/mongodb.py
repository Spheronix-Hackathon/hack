import base64
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure

from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

MONGO_URI = settings.effective_mongodb_uri
DB_NAME = settings.effective_database_name
# Fix L-05 / DB-04: Use configurable global DB name from settings (GLOBAL_DB_NAME env var)
GLOBAL_DB_NAME = settings.global_db_name

# Fix P-03: Remove sync MongoClient created at import time — it was unused (only async is used)
# All DB operations use the async motor client below.
async_client = AsyncIOMotorClient(MONGO_URI)
async_db = async_client[DB_NAME]
global_async_db = async_client[GLOBAL_DB_NAME]

# Primary collections
users_async_collection = async_db["users"]
registrations_async_collection = async_db["registrations"]
teams_async_collection = async_db["teams"]
hackathon_challenges_async_collection = async_db["hackathon_challenges"]

# Global (shared) collections
colleges_async_collection = global_async_db["colleges"]
# The collection name must be "global data" (with a space) to maintain compatibility
# with the other project that updates the task details in this database.
global_data_async_collection = global_async_db["global data"]
branches_async_collection = global_async_db["branches"]
contacts_async_collection = global_async_db["contacts"]


async def initialize_async_collections() -> None:
    # Zero Database Change Rule: Preserve all existing collections, indexes, and records as strictly read-only.
    try:
        await async_client.admin.command("ping")
        logger.info("MongoDB connection verified. Existing collections, indexes, and records remain strictly untouched.")
    except Exception as exc:
        logger.warning("MongoDB ping notice during startup: %s", exc)
    return

    # Helper to recreate index if options have changed (e.g. adding sparse=True)
    async def create_index_safe(collection, key, **kwargs):
        try:
            await collection.create_index(key, **kwargs)
        except Exception as e:
            err_msg = str(e)
            if "IndexKeySpecsConflict" in err_msg or "IndexOptionsConflict" in err_msg or getattr(e, "code", None) in (85, 86):
                logger.info(f"Recreating conflicting index for {key} on {collection.name}")
                try:
                    await collection.drop_index(f"{key}_1")
                except Exception:
                    pass
                await collection.create_index(key, **kwargs)
            else:
                logger.warning(f"Notice on index {key}: {e}")

    # --- Users ---
    await create_index_safe(users_async_collection, "email", unique=True)

    # --- Registrations (primary) ---
    await create_index_safe(registrations_async_collection, "email", unique=True, sparse=True)
    await create_index_safe(registrations_async_collection, "mobile", unique=True, sparse=True)
    await create_index_safe(registrations_async_collection, "rollNumber", unique=True, sparse=True)
    await create_index_safe(registrations_async_collection, "order_id", unique=True, sparse=True)
    await create_index_safe(registrations_async_collection, "rzp_order_id", unique=True, sparse=True)
    await create_index_safe(registrations_async_collection, "participant_id", unique=True, sparse=True)
    await create_index_safe(registrations_async_collection, "registrationCompleted")

    # Fix DB-02: Add missing indexes on nested email/rollNumber/mobile paths
    # These are needed for the duplicate-check $or queries to avoid full-collection scans
    await registrations_async_collection.create_index("leader.email")
    await registrations_async_collection.create_index("leader.rollNumber")
    await registrations_async_collection.create_index("team_members.email")
    await registrations_async_collection.create_index("team_members.rollNumber")
    await registrations_async_collection.create_index("team_members.mobile")

    # --- Teams ---
    await teams_async_collection.create_index("teamId", unique=True)

    # --- Colleges (global) ---
    await colleges_async_collection.create_index("name_lc")
    await colleges_async_collection.create_index("sort_order")

    # --- Contacts (global) ---
    await contacts_async_collection.create_index("email")
    await contacts_async_collection.create_index("timestamp")

    # --- Hackathon challenges ---
    await hackathon_challenges_async_collection.create_index(
        [("category", 1), ("title", 1)], unique=True
    )
    await hackathon_challenges_async_collection.create_index("category")
    await hackathon_challenges_async_collection.create_index("difficulty")

    logger.info("All MongoDB indexes initialized successfully.")

    # --- Ensure strictly single payment_receipt_base64 at root level and remove duplicates ---
    try:
        receipts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads", "receipts")

        # Step 1: Ensure payment_receipt_base64 and payment_receipt_name are populated at root for all records
        cursor = registrations_async_collection.find({})
        async for doc in cursor:
            existing_b64 = (
                doc.get("payment_receipt_base64")
                or doc.get("receipt_base64")
                or (doc.get("payment", {}) or {}).get("payment_receipt_base64")
                or (doc.get("payment", {}) or {}).get("receipt_base64")
            )
            existing_name = (
                doc.get("payment_receipt_name")
                or doc.get("receipt_name")
                or (doc.get("payment", {}) or {}).get("payment_receipt_name")
                or (doc.get("payment", {}) or {}).get("receipt_name")
            )
            rel_url = doc.get("payment_receipt_url") or doc.get("receipt_url") or (doc.get("payment", {}) or {}).get("receipt_url") or ""

            if not existing_b64 and rel_url:
                if "uploads/receipts/" in rel_url:
                    fname = os.path.basename(rel_url.split("?")[0])
                    fpath = os.path.join(receipts_dir, fname)
                    if os.path.exists(fpath):
                        try:
                            with open(fpath, "rb") as rf:
                                raw_bytes = rf.read()
                            ext = os.path.splitext(fname)[1].lower()
                            mime_types = {
                                ".png": "image/png",
                                ".jpg": "image/jpeg",
                                ".jpeg": "image/jpeg",
                                ".webp": "image/webp",
                                ".pdf": "application/pdf",
                            }
                            mt = mime_types.get(ext, "image/png")
                            encoded = base64.b64encode(raw_bytes).decode("utf-8")
                            existing_b64 = f"data:{mt};base64,{encoded}"
                            if not existing_name:
                                existing_name = fname
                        except Exception:
                            pass

            set_fields = {}
            if existing_b64 and doc.get("payment_receipt_base64") != existing_b64:
                set_fields["payment_receipt_base64"] = existing_b64
            if existing_name and doc.get("payment_receipt_name") != existing_name:
                set_fields["payment_receipt_name"] = existing_name

            if set_fields:
                await registrations_async_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": set_fields}
                )

        # Step 2: Unset duplicate receipt fields from inside payment sub-object, leader, and all legacy fields
        await registrations_async_collection.update_many(
            {},
            {
                "$unset": {
                    "payment.payment_receipt_base64": "",
                    "payment.payment_receipt_name": "",
                    "payment.payment_receipt_url": "",
                    "payment.receipt_url": "",
                    "payment.payment_receipt": "",
                    "payment.receipt_base64": "",
                    "payment.receipt_name": "",
                    "payment_receipt_url": "",
                    "receipt_url": "",
                    "payment_receipt": "",
                    "receipt_base64": "",
                    "leader.payment_receipt_url": "",
                    "leader.payment_receipt_base64": "",
                    "leader.payment_receipt_name": "",
                    "leader.receipt_url": "",
                    "leader.payment_receipt": "",
                    "leader.receipt_base64": "",
                }
            }
        )
        logger.info("Successfully cleaned up all duplicate receipt fields; only single payment_receipt_base64 at root is retained.")

        # Step 3: Backfill missing or empty team_members in registrations collection from teams collection
        team_cursor = registrations_async_collection.find({
            "participationMode": "team",
            "$or": [
                {"team_members": {"$exists": False}},
                {"team_members": None},
                {"team_members": {"$size": 0}},
            ]
        })
        async for reg in team_cursor:
            team_id = reg.get("team_id")
            order_id = reg.get("rzp_order_id")
            query_conds = []
            if team_id:
                query_conds.extend([{"teamId": team_id}, {"team_id": team_id}])
            if order_id:
                query_conds.extend([{"registrationId": order_id}, {"rzp_order_id": order_id}])

            if query_conds:
                team_doc = await teams_async_collection.find_one({"$or": query_conds})
                if team_doc and team_doc.get("members"):
                    raw_members = team_doc.get("members", [])
                    leader_email = str(reg.get("leader", {}).get("email") or reg.get("email") or "").lower()

                    extracted_members = []
                    for m in raw_members:
                        m_email = str(m.get("email") or "").lower()
                        m_role = str(m.get("role") or "").lower()
                        if m_role == "leader" or (leader_email and m_email == leader_email):
                            continue
                        extracted_members.append({
                            "name": m.get("name") or m.get("fullName") or "",
                            "email": m_email,
                            "mobile": m.get("mobile") or m.get("phone") or "",
                            "phone": m.get("phone") or m.get("mobile") or "",
                            "rollNumber": m.get("rollNumber") or m.get("roll_number") or "",
                            "githubProfile": m.get("githubProfile") or m.get("github_profile") or None,
                            "branch": m.get("branch") or reg.get("branch") or reg.get("leader", {}).get("branch") or "",
                            "participant_id": m.get("participant_id") or m.get("participantId") or "",
                        })

                    if extracted_members:
                        await registrations_async_collection.update_one(
                            {"_id": reg["_id"]},
                            {"$set": {"team_members": extracted_members}}
                        )
                        logger.info(
                            "Backfilled %d team members for registration %s (Team %s)",
                            len(extracted_members),
                            reg.get("rzp_order_id"),
                            team_id,
                        )

        # Step 4: Ensure single currentYear and remove duplicate current_year fields
        # First backfill currentYear from current_year where currentYear is missing
        async for doc in registrations_async_collection.find({"currentYear": {"$exists": False}, "current_year": {"$exists": True}}):
            if doc.get("current_year"):
                await registrations_async_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"currentYear": doc.get("current_year")}}
                )
        async for doc in registrations_async_collection.find({"leader.currentYear": {"$exists": False}, "leader.current_year": {"$exists": True}}):
            if (doc.get("leader") or {}).get("current_year"):
                await registrations_async_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"leader.currentYear": doc.get("leader", {}).get("current_year")}}
                )

        # Unset duplicate current_year and leader.current_year
        await registrations_async_collection.update_many(
            {},
            {
                "$unset": {
                    "current_year": "",
                    "leader.current_year": ""
                }
            }
        )
        logger.info("Cleaned up duplicate current_year; single currentYear field retained.")

        # Step 5: Backfill order_id from rzp_order_id where order_id is missing
        async for doc in registrations_async_collection.find({"order_id": {"$exists": False}, "rzp_order_id": {"$exists": True}}):
            if doc.get("rzp_order_id"):
                await registrations_async_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"order_id": doc.get("rzp_order_id")}}
                )
        logger.info("Ensured order_id is populated across all registration documents.")

        # Step 6: Normalize Ideathon records to have task_selected and assigned_challenge set strictly to Ideathon
        await registrations_async_collection.update_many(
            {
                "$or": [
                    {"project_selected": {"$regex": "^ideathon$", "$options": "i"}},
                    {"assigned_challenge.category": {"$regex": "^ideathon$", "$options": "i"}},
                ]
            },
            {
                "$set": {
                    "project_selected": "Ideathon",
                    "task_selected": "Ideathon",
                    "assigned_challenge.category": "Ideathon",
                    "assigned_challenge.title": "Ideathon",
                    "assigned_challenge.description": "Design and develop an innovative prototype solution. Present your problem statement, system architecture, and prototype demonstration.",
                    "assigned_challenge.requirements": "Problem Statement, Innovation Pitch, System Architecture, Prototype Demo / GitHub Repository",
                }
            }
        )
        logger.info("Ensured all Ideathon registrations have task_selected and assigned_challenge set strictly to Ideathon.")
    except Exception as e:
        logger.warning("Notice during database migration/cleanup: %s", e)