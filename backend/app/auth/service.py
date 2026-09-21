import uuid
from datetime import datetime, timedelta, timezone

import asyncpg
import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token_hash,
)


class TokenPair:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token


async def signup(pool: asyncpg.Pool, email: str, password: str) -> TokenPair:
    existing = await pool.fetchrow("SELECT id FROM users WHERE email = $1", email)
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with that email already exists")

    password_hash = hash_password(password)
    user = await pool.fetchrow(
        "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
        email,
        password_hash,
    )
    return await _issue_tokens(pool, str(user["id"]))


async def login(pool: asyncpg.Pool, email: str, password: str) -> TokenPair:
    user = await pool.fetchrow("SELECT id, password_hash FROM users WHERE email = $1", email)
    if user is None or not verify_password(password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return await _issue_tokens(pool, str(user["id"]))


async def refresh(pool: asyncpg.Pool, presented_refresh_token: str) -> TokenPair:
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    try:
        payload = decode_token(presented_refresh_token, expected_type="refresh")
    except jwt.PyJWTError:
        raise invalid

    user_id = payload["sub"]
    candidates = await pool.fetch(
        """
        SELECT id, token_hash FROM refresh_tokens
        WHERE user_id = $1 AND revoked_at IS NULL AND expires_at > now()
        """,
        uuid.UUID(user_id),
    )
    matched = next(
        (row for row in candidates if verify_refresh_token_hash(presented_refresh_token, row["token_hash"])),
        None,
    )
    if matched is None:
        raise invalid

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE refresh_tokens SET revoked_at = now() WHERE id = $1", matched["id"]
            )
            return await _issue_tokens(pool, user_id, conn=conn)


async def logout(pool: asyncpg.Pool, presented_refresh_token: str) -> None:
    try:
        payload = decode_token(presented_refresh_token, expected_type="refresh")
    except jwt.PyJWTError:
        return
    user_id = payload["sub"]
    candidates = await pool.fetch(
        "SELECT id, token_hash FROM refresh_tokens WHERE user_id = $1 AND revoked_at IS NULL",
        uuid.UUID(user_id),
    )
    for row in candidates:
        if verify_refresh_token_hash(presented_refresh_token, row["token_hash"]):
            await pool.execute(
                "UPDATE refresh_tokens SET revoked_at = now() WHERE id = $1", row["id"]
            )
            break


async def _issue_tokens(pool: asyncpg.Pool, user_id: str, conn: asyncpg.Connection | None = None) -> TokenPair:
    settings = get_settings()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    executor = conn if conn is not None else pool
    await executor.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
        uuid.UUID(user_id),
        hash_refresh_token(refresh_token),
        expires_at,
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)
