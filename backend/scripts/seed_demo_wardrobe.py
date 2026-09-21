"""Seed a user's wardrobe with placeholder demo items (is_demo_seed=true).

These use plainly-fake geometric placeholder images (not real photos), so they're
inserted directly as already-"done" -- no bg_removal job needed, since there's no
real background to remove and no AI call is warranted for placeholder art.

Usage: python -m scripts.seed_demo_wardrobe <user_email>
"""

import asyncio
import sys
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.db.pool import close_pool, init_pool, get_pool
from app.integrations import color_extract, storage

PLACEHOLDER_DIR = Path(__file__).resolve().parent.parent.parent / "frontend/public/assets/wardrobe/placeholders"

# category -> (clothing_type, style_tags) -- fixed, not AI-assigned, since these
# are placeholder assets rather than real photos worth spending a vision call on.
SEED_ITEMS = {
    "top": ("t-shirt", ["casual", "minimalist"]),
    "bottom": ("jeans", ["casual", "classic"]),
    "dress": ("midi-dress", ["romantic", "classic"]),
    "shoes": ("sneakers", ["casual", "streetwear"]),
    "jacket": ("denim-jacket", ["streetwear", "casual"]),
    "accessory": ("bag", ["classic", "minimalist"]),
}


async def seed(email: str) -> None:
    settings = get_settings()
    pool = await init_pool(settings.database_url)

    user = await pool.fetchrow("SELECT id FROM users WHERE email = $1", email)
    if user is None:
        print(f"No user found with email {email}")
        await close_pool()
        return
    user_id = user["id"]

    async with pool.acquire() as conn:
        for category, (clothing_type, style_tags) in SEED_ITEMS.items():
            image_path = PLACEHOLDER_DIR / f"{category}.png"
            image_bytes = image_path.read_bytes()

            item_id = uuid.uuid4()
            key = f"cutouts/demo/{item_id}.png"
            await storage.upload_bytes(key, image_bytes, "image/png")
            dominant_colors = color_extract.extract_dominant_colors(image_bytes)

            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO wardrobe_items
                        (id, user_id, category, clothing_type, original_image_key, cutout_image_key,
                         cutout_status, dominant_colors, label, is_demo_seed)
                    VALUES ($1, $2, $3, $4, $5, $5, 'done', $6, $7, true)
                    """,
                    item_id,
                    user_id,
                    category,
                    clothing_type,
                    key,
                    dominant_colors,
                    f"Demo {category}",
                )
                if style_tags:
                    await conn.execute(
                        """
                        INSERT INTO wardrobe_item_tags (wardrobe_item_id, style_tag_id)
                        SELECT $1, id FROM style_tags WHERE name = ANY($2::text[])
                        """,
                        item_id,
                        style_tags,
                    )
            print(f"seeded {category}: {item_id}")

    await close_pool()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.seed_demo_wardrobe <user_email>")
        sys.exit(1)
    asyncio.run(seed(sys.argv[1]))
