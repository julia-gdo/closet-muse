import logging
import uuid

import asyncpg

from app.inspiration import repository as inspiration_repo
from app.integrations import color_extract, storage, vision

logger = logging.getLogger("worker")


async def handle_style_analysis(pool: asyncpg.Pool, payload: dict) -> None:
    image_id = uuid.UUID(payload["inspiration_image_id"])
    image = await inspiration_repo.get_image(pool, image_id)
    if image is None:
        return

    image_bytes = await storage.download_bytes(image["image_key"])

    # Deterministic, always-reliable -- never blocked by Gemini's availability.
    dominant_colors = color_extract.extract_dominant_colors(image_bytes)

    # Same graceful-degradation pattern as bg_removal: a transient vision-API
    # failure shouldn't leave the whole image stuck retrying/failed when the
    # colors (the deterministic part) already succeeded.
    try:
        analysis = await vision.analyze_inspiration_image(image_bytes)
    except Exception as exc:  # noqa: BLE001
        logger.warning("style analysis failed for inspiration image %s, continuing untagged: %s", image_id, exc)
        analysis = {"style_tags": [], "summary": None}

    await inspiration_repo.mark_done(
        pool,
        image_id,
        analysis["summary"],
        dominant_colors,
        analysis["style_tags"],
    )
