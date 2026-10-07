import asyncio
from app.database.mongodb import async_db, global_async_db
from bson import ObjectId

async def update_settings_colleges():
    district_colleges = [
        "Srinivasa Ramanujan Institute of Technology (SRIT), Anantapur",
        "P.V.K.K Institute of Technology, Anantapur",
        "GATES Institute of Technology, Anantapur"
    ]
    state_colleges = [
        "Thirumala College of Engineering, Palnadu",
        "PVKK Institute of Technology, Anantapur"
    ]
    best_universities = [
        "Jawaharlal Nehru Technological University Kakinada (JNTUK)",
        "Adikavi Nannaya University",
        "Sri Krishnadevaraya University (SKU)",
        "Aditya University",
        "Vignan's University",
        "Godavari Global University"
    ]

    target_id = ObjectId("6a5602ff3a0f67c08c3d7cfc")
    update_dict = {
        "districtLevelColleges": district_colleges,
        "stateLevelColleges": state_colleges,
        "andhraBestUniversities": best_universities,
        "bestUniversities": best_universities,
        "universityLevelColleges": best_universities,
        "andhraUniversities": best_universities,
        "universities": best_universities,
        "andhra_best_universities": best_universities
    }

    updated = False
    for db in [async_db, global_async_db]:
        try:
            res = await db["settings"].update_one(
                {"_id": target_id},
                {"$set": update_dict}
            )
            if res.matched_count > 0:
                print(f"Successfully updated settings in {db.name} (modified: {res.modified_count})")
                updated = True
        except Exception as e:
            print(f"Error updating in {db.name}: {e}")

    if not updated:
        # Fallback update any settings doc found
        for db in [async_db, global_async_db]:
            try:
                res = await db["settings"].update_many(
                    {},
                    {"$set": update_dict}
                )
                if res.matched_count > 0:
                    print(f"Updated all settings docs in {db.name} (modified: {res.modified_count})")
            except Exception as e:
                print(f"Error in fallback: {e}")

if __name__ == "__main__":
    asyncio.run(update_settings_colleges())
