import httpx

from app.core.config import get_settings


class BackgroundRemovalError(Exception):
    pass


async def remove_background(image_bytes: bytes) -> bytes:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": ("image.jpg", image_bytes)},
            data={"size": "auto"},
            headers={"X-Api-Key": settings.removebg_api_key},
        )
    if response.status_code != 200:
        try:
            detail = response.json()["errors"][0]["title"]
        except Exception:
            detail = response.text
        raise BackgroundRemovalError(detail)
    return response.content
