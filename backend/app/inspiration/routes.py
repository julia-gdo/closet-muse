import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.db.pool import get_pool
from app.inspiration import repository as inspiration_repo
from app.inspiration.schemas import CreateImageRequest, CreateImageResponse, InspirationImageResponse
from app.integrations import storage
from app.jobs import repository as jobs_repo

router = APIRouter(prefix="/inspiration", tags=["inspiration"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _parse_user_id(user_id: str) -> uuid.UUID:
    return uuid.UUID(user_id)


async def _to_response(image: asyncpg.Record, style_tags: list[str]) -> InspirationImageResponse:
    image_url = await storage.generate_presigned_get_url(image["image_key"])
    return InspirationImageResponse(
        id=str(image["id"]),
        analysis_status=image["analysis_status"],
        summary=image["summary"],
        dominant_colors=list(image["dominant_colors"]),
        style_tags=style_tags,
        image_url=image_url,
        created_at=image["created_at"],
    )


@router.post("", response_model=CreateImageResponse)
async def create_image(
    body: CreateImageRequest,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> CreateImageResponse:
    ext = ALLOWED_CONTENT_TYPES.get(body.content_type)
    if ext is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported content type")

    image_id = uuid.uuid4()
    key = f"inspiration/{user_id}/{image_id}.{ext}"

    async with pool.acquire() as conn:
        async with conn.transaction():
            await inspiration_repo.create_image(conn, image_id, _parse_user_id(user_id), key)

    upload_url = await storage.generate_presigned_put_url(key, body.content_type)
    return CreateImageResponse(image_id=str(image_id), upload_url=upload_url)


@router.post("/{image_id}/confirm-upload", response_model=InspirationImageResponse)
async def confirm_upload(
    image_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> InspirationImageResponse:
    image = await inspiration_repo.get_image_for_user(pool, image_id, _parse_user_id(user_id))
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    if image["analysis_status"] != "awaiting_upload":
        raise HTTPException(status.HTTP_409_CONFLICT, "Image is not awaiting upload")

    if not await storage.object_exists(image["image_key"]):
        raise HTTPException(status.HTTP_409_CONFLICT, "Upload not found — retry the upload before confirming")

    async with pool.acquire() as conn:
        async with conn.transaction():
            await inspiration_repo.mark_awaiting_upload_confirmed_pending(conn, image_id)
            await jobs_repo.enqueue_job(conn, "style_analysis", {"inspiration_image_id": str(image_id)})

    updated = await inspiration_repo.get_image(pool, image_id)
    tags = await inspiration_repo.get_style_tags_for_images(pool, [image_id])
    return await _to_response(updated, tags[image_id])


@router.get("", response_model=list[InspirationImageResponse])
async def list_images(
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[InspirationImageResponse]:
    images = await inspiration_repo.list_images_for_user(pool, _parse_user_id(user_id))
    tags_by_image = await inspiration_repo.get_style_tags_for_images(pool, [img["id"] for img in images])
    return [await _to_response(img, tags_by_image[img["id"]]) for img in images]


@router.get("/{image_id}", response_model=InspirationImageResponse)
async def get_image(
    image_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> InspirationImageResponse:
    image = await inspiration_repo.get_image_for_user(pool, image_id, _parse_user_id(user_id))
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    tags = await inspiration_repo.get_style_tags_for_images(pool, [image_id])
    return await _to_response(image, tags[image_id])


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> None:
    image = await inspiration_repo.get_image_for_user(pool, image_id, _parse_user_id(user_id))
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    await inspiration_repo.delete_image(pool, image_id, _parse_user_id(user_id))
    if image["image_key"]:
        await storage.delete_object(image["image_key"])
