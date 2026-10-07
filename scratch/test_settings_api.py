import asyncio
import json
from app.routers.settings import get_public_settings

async def main():
    try:
        response = await get_public_settings()
        # response is a JSONResponse
        body_bytes = response.body
        body_str = body_bytes.decode("utf-8")
        parsed = json.loads(body_str)
        print("SUCCESS! API returned status 200 with data:")
        print("stateLevelColleges:", parsed.get("stateLevelColleges"))
        print("districtLevelColleges:", parsed.get("districtLevelColleges"))
        print("andhraBestUniversities:", parsed.get("andhraBestUniversities"))
        with open("scratch/api_test_output.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(parsed, indent=2))
        print("Saved output to scratch/api_test_output.json")
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
