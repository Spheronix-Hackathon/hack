import asyncio
import os
import sys
from datetime import datetime
import uuid

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.mongodb import (
    async_db, 
    users_collection, 
    nodal_registrations_collection,
    submissions_collection
)

async def migrate_submissions():
    print("Starting migration of submissions...")
    
    # 1. Drop the unique index on userId if it exists
    try:
        indexes = await submissions_collection.index_information()
        if 'userId_1' in indexes:
            print("Dropping unique index 'userId_1' on submissions_collection...")
            await submissions_collection.drop_index('userId_1')
            print("Index dropped.")
    except Exception as e:
        print(f"Error checking/dropping index: {e}")
        
    # Create non-unique index
    await submissions_collection.create_index("userId")
    print("Created non-unique index on userId in submissions_collection.")

    collections_to_check = [
        (nodal_registrations_collection, 'principalId'),
        (nodal_registrations_collection, 'nodalOfficerId'),
        (users_collection, 'userId')
    ]
    
    migrated_count = 0
    
    for collection, id_field in collections_to_check:
        # Find users who have completed submissions stored directly in their user document
        cursor = collection.find({"status": "Completed"})
        async for user in cursor:
            # We don't know exactly which ID field was used if it's nodal registrations,
            # but we can check which one is present.
            user_id = user.get("principalId") or user.get("nodalOfficerId") or user.get("userId")
            
            if not user_id:
                continue
                
            # Check if we already migrated this (in case script run multiple times)
            existing = await submissions_collection.find_one({"userId": user_id, "migrated_from_user": True})
            if existing:
                continue
                
            print(f"Migrating submission for user: {user_id}")
            
            # Generate a new submission ID
            timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            random_str = uuid.uuid4().hex[:6].upper()
            submission_id = f"SUB-{timestamp_str}-{random_str}"
            
            submission_doc = {
                "submissionId": submission_id,
                "userId": user_id,
                "status": "Submitted",
                "csvData": user.get("csvData", []),
                "paymentProof": user.get("paymentProof", ""),
                "totalAmount": user.get("totalAmount", 0),
                "eligibleRecords": user.get("eligibleRecords", 0),
                "paymentTimestamp": user.get("paymentTimestamp", datetime.utcnow()),
                "originalFilename": user.get("originalFilename", "Legacy_Submission.xlsx"),
                "migrated_from_user": True
            }
            
            await submissions_collection.insert_one(submission_doc)
            
            # Unset the fields from the user document to complete the transition
            await collection.update_one(
                {"_id": user["_id"]},
                {"$unset": {
                    "status": "",
                    "csvData": "",
                    "paymentProof": "",
                    "totalAmount": "",
                    "eligibleRecords": "",
                    "paymentTimestamp": "",
                    "originalFilename": ""
                }}
            )
            migrated_count += 1
            
    print(f"Migration completed! Migrated {migrated_count} submissions.")

if __name__ == "__main__":
    asyncio.run(migrate_submissions())
