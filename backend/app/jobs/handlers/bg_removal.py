import logging
import uuid

import asyncpg

from app.integrations import color_extract, removebg, storage, vision
from app.wardrobe import repository as wardrobe_repo

logger = logging.getLogger("worker")


async def handle_bg_removal(pool: asyncpg.Pool, payload: dict) -> None:
    item_id = uuid.UUID(payload["wardrobe_item_id"])
    item = await wardrobe_repo.get_item(pool, item_id)
    if item is None:
        return

    original_bytes = await storage.download_bytes(item["original_image_key"])
    cutout_bytes = await removebg.remove_background(original_bytes)

    cutout_key = f"cutouts/{item_id}.png"
    await storage.upload_bytes(cutout_key, cutout_bytes, "image/png")

    dominant_colors = color_extract.extract_dominant_colors(cutout_bytes)

    # AI tagging is an enhancement, not core functionality -- background removal
    # (the part the user is actually waiting on) already succeeded above, so a
    # transient vision-API failure shouldn't fail the whole job and leave the
    # item stuck in needs_fix. Degrade to untagged rather than block.
    try:
        tags = await vision.tag_wardrobe_item(cutout_bytes, item["category"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("style tagging failed for item %s, continuing untagged: %s", item_id, exc)
        tags = {"clothing_type": None, "style_tags": []}

    await wardrobe_repo.mark_done(
        pool,
        item_id,
        cutout_key,
        dominant_colors,
        tags["clothing_type"],
        tags["style_tags"],
    )
