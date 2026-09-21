from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.core.config import get_settings
from app.db.pool import close_pool, init_pool
from app.inspiration.routes import router as inspiration_router
from app.wardrobe.routes import router as wardrobe_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_pool(settings.database_url)
    yield
    await close_pool()


app = FastAPI(title="Closet Muse API", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(wardrobe_router)
app.include_router(inspiration_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
