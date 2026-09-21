import uuid

import asyncpg
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from app.core.security import verify_supabase_token
from app.db.pool import get_pool

_bearer_scheme = HTTPBearer(auto_error=False)

# Users we've already made sure exist in our `users` table this process. Supabase owns
# identity; our table is just a local profile row for foreign keys, created on first sight.
_known_user_ids: set[str] = set()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    pool: asyncpg.Pool = Depends(get_pool),
) -> str:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    try:
        claims = await run_in_threadpool(verify_supabase_token, credentials.credentials)
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Could not reach the auth provider")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token")

    user_id = claims["sub"]
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid access token subject")

    if user_id not in _known_user_ids:
        email = claims.get("email")
        if not email:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Access token has no email")
        await pool.execute(
            """
            INSERT INTO users (id, email) VALUES ($1, $2)
            ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, updated_at = now()
            """,
            uuid.UUID(user_id),
            email,
        )
        _known_user_ids.add(user_id)
    return user_id


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pool),
) -> asyncpg.Record:
    user = await pool.fetchrow("SELECT id, email FROM users WHERE id = $1", uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user
