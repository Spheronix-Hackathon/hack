import logging

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

# Global (shared) collections
contacts_async_collection = global_async_db["contacts"]

# Nodal Registrations
nodal_registrations_collection = async_db["nodal_registrations"]

# Admin Portal Integration
users_collection = global_async_db["users"]
settings_collection = async_db["settings"]
submissions_collection = async_db["submissions"]


async def initialize_async_collections() -> None:
    # --- Contacts (global) ---
    await contacts_async_collection.create_index("email")
    await contacts_async_collection.create_index("timestamp")

    # --- Nodal Registrations ---
    await nodal_registrations_collection.create_index("collegeCode", unique=True)
    await nodal_registrations_collection.create_index("principalName", unique=True)
    await nodal_registrations_collection.create_index("principalEmail", unique=True)
    await nodal_registrations_collection.create_index("principalMobile", unique=True)
    await nodal_registrations_collection.create_index("nodalOfficerName", unique=True)
    await nodal_registrations_collection.create_index("nodalOfficerEmail", unique=True)
    await nodal_registrations_collection.create_index("nodalOfficerMobile", unique=True)
    await nodal_registrations_collection.create_index("nodalOfficerMobile", unique=True)

    # --- Admin Users & Submissions ---
    await users_collection.create_index("userId", unique=True)
    await submissions_collection.create_index("userId")

    # --- Initialize andhraBestUniversities field if missing ---
    try:
        curr_settings = await settings_collection.find_one({})
        if curr_settings and not any(k in curr_settings for k in ["andhraBestUniversities", "bestUniversities", "universityLevelColleges"]):
            await settings_collection.update_one(
                {"_id": curr_settings["_id"]},
                {"$set": {
                    "andhraBestUniversities": ["kvsrit, Kurnool"],
                    "bestUniversities": ["kvsrit, Kurnool"],
                    "universityLevelColleges": ["kvsrit, Kurnool"],
                    "andhraUniversities": ["kvsrit, Kurnool"],
                    "universities": ["kvsrit, Kurnool"],
                }}
            )
            logger.info("Initialized default andhraBestUniversities in settings collection.")
    except Exception as e:
        logger.warning(f"Could not check/initialize andhraBestUniversities: {e}")

    logger.info("All MongoDB indexes initialized successfully.")