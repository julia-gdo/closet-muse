import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.db.pool import get_pool
from app.integrations import storage
from app.jobs import repository as jobs_repo
from app.wardrobe import repository as wardrobe_repo
from app.wardrobe.schemas import (
    CreateItemRequest,
    CreateItemResponse,
    UpdateItemRequest,
    WardrobeItemResponse,
)

router = APIRouter(prefix="/wardrobe/items", tags=["wardrobe"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _parse_user_id(user_id: str) -> uuid.UUID:
    return uuid.UUID(user_id)


async def _to_response(item: asyncpg.Record, style_tags: list[str]) -> WardrobeItemResponse:
    original_url = await storage.generate_presigned_get_url(item["original_image_key"])
    cutout_url = (
        await storage.generate_presigned_get_url(item["cutout_image_key"])
        if item["cutout_image_key"]
        else None
    )
    return WardrobeItemResponse(
        id=str(item["id"]),
        category=item["category"],
        clothing_type=item["clothing_type"],
        cutout_status=item["cutout_status"],
        cutout_error=item["cutout_error"],
        dominant_colors=list(item["dominant_colors"]),
        label=item["label"],
        style_tags=style_tags,
        original_image_url=original_url,
        cutout_image_url=cutout_url,
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


@router.post("", response_model=CreateItemResponse)
async def create_item(
    body: CreateItemRequest,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> CreateItemResponse:
    ext = ALLOWED_CONTENT_TYPES.get(body.content_type)
    if ext is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported content type")

    item_id = uuid.uuid4()
    key = f"originals/{user_id}/{item_id}.{ext}"

    async with pool.acquire() as conn:
        async with conn.transaction():
            await wardrobe_repo.create_item(conn, item_id, _parse_user_id(user_id), body.category, key, body.label)

    upload_url = await storage.generate_presigned_put_url(key, body.content_type)
    return CreateItemResponse(item_id=str(item_id), upload_url=upload_url)


@router.post("/{item_id}/confirm-upload", response_model=WardrobeItemResponse)
async def confirm_upload(
    item_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> WardrobeItemResponse:
    item = await wardrobe_repo.get_item_for_user(pool, item_id, _parse_user_id(user_id))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    if item["cutout_status"] != "awaiting_upload":
        raise HTTPException(status.HTTP_409_CONFLICT, "Item is not awaiting upload")

    if not await storage.object_exists(item["original_image_key"]):
        raise HTTPException(status.HTTP_409_CONFLICT, "Upload not found — retry the upload before confirming")

    async with pool.acquire() as conn:
        async with conn.transaction():
            await wardrobe_repo.mark_awaiting_upload_confirmed_pending(conn, item_id)
            await jobs_repo.enqueue_job(conn, "bg_removal", {"wardrobe_item_id": str(item_id)})

    updated = await wardrobe_repo.get_item(pool, item_id)
    tags = await wardrobe_repo.get_style_tags_for_items(pool, [item_id])
    return await _to_response(updated, tags[item_id])


@router.get("", response_model=list[WardrobeItemResponse])
async def list_items(
    category: str | None = None,
    cutout_status: str | None = None,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[WardrobeItemResponse]:
    items = await wardrobe_repo.list_items_for_user(pool, _parse_user_id(user_id), category, cutout_status)
    tags_by_item = await wardrobe_repo.get_style_tags_for_items(pool, [item["id"] for item in items])
    return [await _to_response(item, tags_by_item[item["id"]]) for item in items]


@router.get("/{item_id}", response_model=WardrobeItemResponse)
async def get_item(
    item_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> WardrobeItemResponse:
    item = await wardrobe_repo.get_item_for_user(pool, item_id, _parse_user_id(user_id))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    tags = await wardrobe_repo.get_style_tags_for_items(pool, [item_id])
    return await _to_response(item, tags[item_id])


@router.patch("/{item_id}", response_model=WardrobeItemResponse)
async def update_item(
    item_id: uuid.UUID,
    body: UpdateItemRequest,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> WardrobeItemResponse:
    updated = await wardrobe_repo.update_item(pool, item_id, _parse_user_id(user_id), body.label, body.category)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    tags = await wardrobe_repo.get_style_tags_for_items(pool, [item_id])
    return await _to_response(updated, tags[item_id])


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> None:
    item = await wardrobe_repo.get_item_for_user(pool, item_id, _parse_user_id(user_id))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    await wardrobe_repo.delete_item(pool, item_id, _parse_user_id(user_id))
    if item["original_image_key"]:
        await storage.delete_object(item["original_image_key"])
    if item["cutout_image_key"]:
        await storage.delete_object(item["cutout_image_key"])


@router.post("/{item_id}/retry-background-removal", response_model=WardrobeItemResponse)
async def retry_background_removal(
    item_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> WardrobeItemResponse:
    item = await wardrobe_repo.get_item_for_user(pool, item_id, _parse_user_id(user_id))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    if item["cutout_status"] != "needs_fix":
        raise HTTPException(status.HTTP_409_CONFLICT, "Item is not in a failed state")

    async with pool.acquire() as conn:
        async with conn.transaction():
            await wardrobe_repo.reset_for_retry(conn, item_id)
            await jobs_repo.enqueue_job(conn, "bg_removal", {"wardrobe_item_id": str(item_id)})

    updated = await wardrobe_repo.get_item(pool, item_id)
    tags = await wardrobe_repo.get_style_tags_for_items(pool, [item_id])
    return await _to_response(updated, tags[item_id])
