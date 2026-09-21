from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from botocore.exceptions import ClientError

from app.core.config import get_settings

_session = get_session()


@asynccontextmanager
async def _client():
    settings = get_settings()
    endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    async with _session.create_client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    ) as client:
        yield client


async def generate_presigned_put_url(key: str, content_type: str, expires_in: int = 900) -> str:
    settings = get_settings()
    async with _client() as client:
        return await client.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.r2_bucket_name, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )


async def generate_presigned_get_url(key: str, expires_in: int = 900) -> str:
    settings = get_settings()
    async with _client() as client:
        return await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.r2_bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )


async def object_exists(key: str) -> bool:
    settings = get_settings()
    async with _client() as client:
        try:
            await client.head_object(Bucket=settings.r2_bucket_name, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise


async def download_bytes(key: str) -> bytes:
    settings = get_settings()
    async with _client() as client:
        response = await client.get_object(Bucket=settings.r2_bucket_name, Key=key)
        return await response["Body"].read()


async def upload_bytes(key: str, data: bytes, content_type: str) -> None:
    settings = get_settings()
    async with _client() as client:
        await client.put_object(Bucket=settings.r2_bucket_name, Key=key, Body=data, ContentType=content_type)


async def delete_object(key: str) -> None:
    settings = get_settings()
    async with _client() as client:
        await client.delete_object(Bucket=settings.r2_bucket_name, Key=key)
