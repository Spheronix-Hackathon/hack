import asyncio
from app.database.mongodb import settings_collection

async def main():
    docs = await settings_collection.find({}).to_list(None)
    for doc in docs:
        print(doc)

if __name__ == "__main__":
    asyncio.run(main())
