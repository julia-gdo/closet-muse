import uuid

import asyncpg


async def create_item(
    conn: asyncpg.Connection,
    item_id: uuid.UUID,
    user_id: uuid.UUID,
    category: str,
    original_image_key: str,
    label: str | None,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO wardrobe_items (id, user_id, category, original_image_key, label)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        item_id,
        user_id,
        category,
        original_image_key,
        label,
    )


async def get_item(pool: asyncpg.Pool, item_id: uuid.UUID) -> asyncpg.Record | None:
    return await pool.fetchrow("SELECT * FROM wardrobe_items WHERE id = $1", item_id)


async def get_item_for_user(pool: asyncpg.Pool, item_id: uuid.UUID, user_id: uuid.UUID) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM wardrobe_items WHERE id = $1 AND user_id = $2", item_id, user_id
    )


async def list_items_for_user(
    pool: asyncpg.Pool, user_id: uuid.UUID, category: str | None = None, cutout_status: str | None = None
) -> list[asyncpg.Record]:
    query = "SELECT * FROM wardrobe_items WHERE user_id = $1"
    params: list = [user_id]
    if category is not None:
        params.append(category)
        query += f" AND category = ${len(params)}"
    if cutout_status is not None:
        params.append(cutout_status)
        query += f" AND cutout_status = ${len(params)}"
    query += " ORDER BY created_at DESC"
    return await pool.fetch(query, *params)


async def delete_item(pool: asyncpg.Pool, item_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await pool.execute(
        "DELETE FROM wardrobe_items WHERE id = $1 AND user_id = $2", item_id, user_id
    )
    return result.endswith("1")


async def mark_awaiting_upload_confirmed_pending(conn: asyncpg.Connection, item_id: uuid.UUID) -> None:
    await conn.execute(
        "UPDATE wardrobe_items SET cutout_status = 'pending', updated_at = now() WHERE id = $1",
        item_id,
    )


async def reset_for_retry(conn: asyncpg.Connection, item_id: uuid.UUID) -> None:
    await conn.execute(
        """
        UPDATE wardrobe_items
        SET cutout_status = 'pending', cutout_error = NULL, updated_at = now()
        WHERE id = $1
        """,
        item_id,
    )


async def mark_done(
    pool: asyncpg.Pool,
    item_id: uuid.UUID,
    cutout_image_key: str,
    dominant_colors: list[str],
    clothing_type: str | None,
    style_tag_names: list[str],
) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE wardrobe_items
                SET cutout_status = 'done', cutout_image_key = $2, dominant_colors = $3,
                    clothing_type = $4, cutout_error = NULL, updated_at = now()
                WHERE id = $1
                """,
                item_id,
                cutout_image_key,
                dominant_colors,
                clothing_type,
            )
            if style_tag_names:
                await conn.execute(
                    """
                    INSERT INTO wardrobe_item_tags (wardrobe_item_id, style_tag_id)
                    SELECT $1, id FROM style_tags WHERE name = ANY($2::text[])
                    ON CONFLICT DO NOTHING
                    """,
                    item_id,
                    style_tag_names,
                )


async def mark_needs_fix(pool: asyncpg.Pool, item_id: uuid.UUID, error: str) -> None:
    await pool.execute(
        "UPDATE wardrobe_items SET cutout_status = 'needs_fix', cutout_error = $2, updated_at = now() WHERE id = $1",
        item_id,
        error,
    )


async def update_item(
    pool: asyncpg.Pool, item_id: uuid.UUID, user_id: uuid.UUID, label: str | None, category: str | None
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        UPDATE wardrobe_items
        SET label = COALESCE($3, label),
            category = COALESCE($4, category),
            -- a category change can invalidate the AI-assigned clothing_type
            -- (it's only valid within its original category's vocabulary)
            clothing_type = CASE WHEN $4 IS NOT NULL AND $4 != category THEN NULL ELSE clothing_type END,
            updated_at = now()
        WHERE id = $1 AND user_id = $2
        RETURNING *
        """,
        item_id,
        user_id,
        label,
        category,
    )


async def get_style_tags_for_items(pool: asyncpg.Pool, item_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[str]]:
    if not item_ids:
        return {}
    rows = await pool.fetch(
        """
        SELECT wit.wardrobe_item_id, st.name
        FROM wardrobe_item_tags wit
        JOIN style_tags st ON st.id = wit.style_tag_id
        WHERE wit.wardrobe_item_id = ANY($1::uuid[])
        """,
        item_ids,
    )
    result: dict[uuid.UUID, list[str]] = {item_id: [] for item_id in item_ids}
    for row in rows:
        result[row["wardrobe_item_id"]].append(row["name"])
    return result
