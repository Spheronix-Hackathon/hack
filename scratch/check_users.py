import asyncio
from app.database.mongodb import users_collection

async def main():
    docs = await users_collection.find({}, {'password': 0, 'totpSecret': 0}).to_list(100)
    print("Users found:", len(docs))
    for d in docs:
        print(d)

if __name__ == "__main__":
    asyncio.run(main())
