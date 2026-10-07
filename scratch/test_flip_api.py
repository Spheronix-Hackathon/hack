import asyncio
from app.routers.flip_images import get_current_flip_images, DEFAULT_FLIP_IMAGES
from app.routers.settings import get_public_settings
import json

async def main():
    print("Testing get_current_flip_images()...")
    images = await get_current_flip_images()
    print(f"Retrieved {len(images)} flip images:")
    for img in images:
        print(" -", img)

    print("\nTesting get_public_settings()...")
    resp = await get_public_settings()
    data = json.loads(resp.body.decode('utf-8'))
    print("Has flipImages in public settings response?", "flipImages" in data)
    print(f"Public settings flipImages count: {len(data.get('flipImages', []))}")
    if data.get('flipImages'):
        print("Sample flipImage:", data['flipImages'][0])

if __name__ == "__main__":
    asyncio.run(main())
