import asyncio
from app.services.auth_service import AuthService
from app.routers.flip_images import admin_add_flip_image_link, admin_delete_flip_image, admin_reset_default_flip_images, LinkImageRequest, get_current_flip_images

async def test_admin_flow():
    token = AuthService.create_jwt_token({"userId": "admin", "role": "admin"})
    auth_header = f"Bearer {token}"
    print("Generated test admin token successfully.")

    # 1. Add image link
    req = LinkImageRequest(url="https://images.unsplash.com/photo-1531482615713-2afd69097998", title="AI Hackathon Hall")
    res1 = await admin_add_flip_image_link(req, authorization=auth_header)
    print("Added image link:", res1["success"], "Total images:", len(res1["images"]))
    new_id = res1["image"]["id"]

    # 2. Check current flip images
    cur = await get_current_flip_images()
    print(f"Current images in DB: {len(cur)}. Last image title: {cur[-1]['title']}")

    # 3. Delete the added image
    res2 = await admin_delete_flip_image(image_id=new_id, authorization=auth_header)
    print("Deleted image:", res2["success"], "Remaining images:", len(res2["images"]))

    # 4. Reset to defaults
    res3 = await admin_reset_default_flip_images(authorization=auth_header)
    print("Reset to defaults:", res3["success"], "Total images:", len(res3["images"]))

if __name__ == "__main__":
    asyncio.run(test_admin_flow())
