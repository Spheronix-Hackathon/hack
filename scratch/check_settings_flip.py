import asyncio
from app.database.mongodb import settings_collection

async def main():
    doc = await settings_collection.find_one({})
    print("Has flipImages in doc?", "flipImages" in (doc or {}))
    if doc and "flipImages" in doc:
        print("flipImages:", doc["flipImages"])

if __name__ == "__main__":
    asyncio.run(main())
