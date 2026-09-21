import uuid

import asyncpg


async def create_image(
    conn: asyncpg.Connection, image_id: uuid.UUID, user_id: uuid.UUID, image_key: str
) -> asyncpg.Record:
    return await conn.fetchrow(
        "INSERT INTO inspiration_images (id, user_id, image_key) VALUES ($1, $2, $3) RETURNING *",
        image_id,
        user_id,
        image_key,
    )


async def get_image(pool: asyncpg.Pool, image_id: uuid.UUID) -> asyncpg.Record | None:
    return await pool.fetchrow("SELECT * FROM inspiration_images WHERE id = $1", image_id)


async def get_image_for_user(pool: asyncpg.Pool, image_id: uuid.UUID, user_id: uuid.UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM inspiration_images WHERE id = $1 AND user_id = $2", image_id, user_id
    )


async def list_images_for_user(pool: asyncpg.Pool, user_id: uuid.UUID) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM inspiration_images WHERE user_id = $1 ORDER BY created_at DESC", user_id
    )


async def delete_image(pool: asyncpg.Pool, image_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await pool.execute(
        "DELETE FROM inspiration_images WHERE id = $1 AND user_id = $2", image_id, user_id
    )
    return result.endswith("1")


async def mark_awaiting_upload_confirmed_pending(conn: asyncpg.Connection, image_id: uuid.UUID) -> None:
    await conn.execute(
        "UPDATE inspiration_images SET analysis_status = 'pending' WHERE id = $1", image_id
    )


async def mark_done(
    pool: asyncpg.Pool, image_id: uuid.UUID, summary: str | None, dominant_colors: list[str], style_tag_names: list[str]
) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE inspiration_images
                SET analysis_status = 'done', summary = $2, dominant_colors = $3
                WHERE id = $1
                """,
                image_id,
                summary,
                dominant_colors,
            )
            if style_tag_names:
                await conn.execute(
                    """
                    INSERT INTO inspiration_image_tags (inspiration_image_id, style_tag_id)
                    SELECT $1, id FROM style_tags WHERE name = ANY($2::text[])
                    ON CONFLICT DO NOTHING
                    """,
                    image_id,
                    style_tag_names,
                )


async def mark_failed(pool: asyncpg.Pool, image_id: uuid.UUID) -> None:
    await pool.execute("UPDATE inspiration_images SET analysis_status = 'failed' WHERE id = $1", image_id)


async def get_style_tags_for_images(pool: asyncpg.Pool, image_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[str]]:
    if not image_ids:
        return {}
    rows = await pool.fetch(
        """
        SELECT iit.inspiration_image_id, st.name
        FROM inspiration_image_tags iit
        JOIN style_tags st ON st.id = iit.style_tag_id
        WHERE iit.inspiration_image_id = ANY($1::uuid[])
        """,
        image_ids,
    )
    result: dict[uuid.UUID, list[str]] = {image_id: [] for image_id in image_ids}
    for row in rows:
        result[row["inspiration_image_id"]].append(row["name"])
    return result
