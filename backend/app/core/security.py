from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import get_settings


def _auth_base_url() -> str:
    return f"{get_settings().supabase_url.rstrip('/')}/auth/v1"


@lru_cache
def _jwks_client() -> PyJWKClient:
    # Supabase signs user tokens with an asymmetric key and publishes the public half
    # here. PyJWKClient caches the key set, so the network is only hit on first use,
    # on expiry, or when a token carries a key id we haven't seen (key rotation).
    return PyJWKClient(f"{_auth_base_url()}/.well-known/jwks.json", lifespan=3600, timeout=10)


def verify_supabase_token(token: str) -> dict[str, Any]:
    """Blocking (may fetch the JWKS) -- call via run_in_threadpool from async code.
    Raises jwt.PyJWTError if the token is invalid, expired, or not from our project."""
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=_auth_base_url(),
        options={"require": ["exp", "sub"]},
    )
