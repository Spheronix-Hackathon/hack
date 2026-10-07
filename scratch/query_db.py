import pymongo
import json
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

uri = "mongodb://jntua-hackathon:Spheronix%40123%24@ac-qyruoal-shard-00-00.f0qglib.mongodb.net:27017,ac-qyruoal-shard-00-01.f0qglib.mongodb.net:27017,ac-qyruoal-shard-00-02.f0qglib.mongodb.net:27017/spheronix_db?ssl=true&replicaSet=atlas-kcc5yy-shard-0&authSource=admin&appName=jntua-hackathon"
client = pymongo.MongoClient(uri)
db = client['spheronix_db']

output = []
output.append("=== COLLECTIONS IN spheronix_db ===")
colls = db.list_collection_names()
output.append(str(colls))

output.append("\n=== SETTINGS COLLECTION DOCUMENTS ===")
settings_docs = list(db['settings'].find({}))
output.append(json.dumps(settings_docs, indent=2, cls=JSONEncoder))

output.append("\n=== SEARCHING FOR 'kvsrit' ACROSS ALL COLLECTIONS ===")
found_kvsrit = False
for coll_name in colls:
    coll = db[coll_name]
    for doc in coll.find():
        doc_str = json.dumps(doc, cls=JSONEncoder)
        if 'kvsrit' in doc_str.lower():
            output.append(f"Found in {coll_name}: {doc_str}")
            found_kvsrit = True

if not found_kvsrit:
    output.append("Not found in any collection.")

result_text = "\n".join(output)
print(result_text)
try:
    with open("scratch/query_output.txt", "w", encoding="utf-8") as f:
        f.write(result_text)
except Exception as e:
    print(f"File write error: {e}")

