import asyncio
import pymongo
from pymongo import MongoClient

uri = "mongodb://jntua-hackathon:Spheronix%40123%24@ac-qyruoal-shard-00-00.f0qglib.mongodb.net:27017,ac-qyruoal-shard-00-01.f0qglib.mongodb.net:27017,ac-qyruoal-shard-00-02.f0qglib.mongodb.net:27017/spheronix_db?ssl=true&replicaSet=atlas-kcc5yy-shard-0&authSource=admin&appName=jntua-hackathon"

client = MongoClient(uri)
db = client["spheronix_db"]
settings_coll = db["settings"]

doc = settings_coll.find_one({}) or {}
print("Current document before update:")
print(doc)

# Save under all candidate university keys so no matter which key is fetched, it works!
update_fields = {
    "andhraBestUniversities": ["kvsrit, Kurnool"],
    "bestUniversities": ["kvsrit, Kurnool"],
    "universityLevelColleges": ["kvsrit, Kurnool"],
    "andhraUniversities": ["kvsrit, Kurnool"],
    "universities": ["kvsrit, Kurnool"],
    "andhra_best_universities": ["kvsrit, Kurnool"],
}

res = settings_coll.update_one({}, {"$set": update_fields}, upsert=True)
print("\nUpdate result:", res.modified_count, "modified,", res.upserted_id, "upserted")

updated_doc = settings_coll.find_one({})
print("\nUpdated document in MongoDB Atlas:")
print(updated_doc)
