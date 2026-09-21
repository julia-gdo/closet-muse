import asyncpg
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status

from app.auth import service
from app.auth.dependencies import get_current_user
from app.auth.schemas import AccessTokenResponse, LoginRequest, SignupRequest
from app.core.config import get_settings
from app.core.security import csrf_tokens_match, generate_csrf_token
from app.db.pool import get_pool

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"


def _cookie_kwargs() -> dict:
    settings = get_settings()
    is_prod = settings.environment != "development"
    return {
        "secure": is_prod,
        "samesite": "none" if is_prod else "lax",
    }


def _set_auth_cookies(response: Response, refresh_token: str) -> None:
    kwargs = _cookie_kwargs()
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        path="/auth",
        **kwargs,
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        generate_csrf_token(),
        httponly=False,
        path="/",
        **kwargs,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/auth")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


@router.post("/signup", response_model=AccessTokenResponse)
async def signup(
    body: SignupRequest, response: Response, pool: asyncpg.Pool = Depends(get_pool)
) -> AccessTokenResponse:
    tokens = await service.signup(pool, body.email, body.password)
    _set_auth_cookies(response, tokens.refresh_token)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    body: LoginRequest, response: Response, pool: asyncpg.Pool = Depends(get_pool)
) -> AccessTokenResponse:
    tokens = await service.login(pool, body.email, body.password)
    _set_auth_cookies(response, tokens.refresh_token)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    pool: asyncpg.Pool = Depends(get_pool),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    csrf_cookie: str | None = Cookie(default=None, alias=CSRF_COOKIE_NAME),
    x_csrf_token: str | None = Header(default=None),
) -> AccessTokenResponse:
    if refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token cookie present")
    if not csrf_tokens_match(csrf_cookie, x_csrf_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token missing or invalid")

    tokens = await service.refresh(pool, refresh_token)
    _set_auth_cookies(response, tokens.refresh_token)
    return AccessTokenResponse(access_token=tokens.access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    pool: asyncpg.Pool = Depends(get_pool),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
) -> None:
    if refresh_token is not None:
        await service.logout(pool, refresh_token)
    _clear_auth_cookies(response)


@router.get("/me")
async def me(user: asyncpg.Record = Depends(get_current_user)) -> dict:
    return {"id": str(user["id"]), "email": user["email"]}
