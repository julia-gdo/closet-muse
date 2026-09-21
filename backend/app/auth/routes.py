import asyncpg
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# Signup, login, refresh and logout are handled by Supabase Auth in the browser;
# this API only verifies the resulting access token (see dependencies.py).
@router.get("/me")
async def me(user: asyncpg.Record = Depends(get_current_user)) -> dict:
    return {"id": str(user["id"]), "email": user["email"]}
