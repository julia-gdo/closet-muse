import asyncio
import logging
import uuid

import asyncpg

from app.core.config import get_settings
from app.db.pool import close_pool, init_pool
from app.inspiration import repository as inspiration_repo
from app.jobs import repository as jobs_repo
from app.jobs.handlers.bg_removal import handle_bg_removal
from app.jobs.handlers.style_analysis import handle_style_analysis
from app.wardrobe import repository as wardrobe_repo

POLL_INTERVAL_SECONDS = 2

HANDLERS = {
    "bg_removal": handle_bg_removal,
    "style_analysis": handle_style_analysis,
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s worker %(levelname)s %(message)s")
logger = logging.getLogger("worker")


async def process_job(pool: asyncpg.Pool, job: asyncpg.Record) -> None:
    handler = HANDLERS[job["job_type"]]
    try:
        await handler(pool, job["payload"])
        await jobs_repo.mark_job_done(pool, job["id"])
        logger.info("job %s (%s) done", job["id"], job["job_type"])
    except Exception as exc:  # noqa: BLE001 -- any handler failure must be caught to retry/fail the job
        will_retry = await jobs_repo.mark_job_failed_or_retry(
            pool, job["id"], job["attempts"], job["max_attempts"], str(exc)
        )
        logger.warning(
            "job %s (%s) failed (attempt %s/%s): %s -- %s",
            job["id"],
            job["job_type"],
            job["attempts"],
            job["max_attempts"],
            exc,
            "will retry" if will_retry else "terminally failed",
        )
        if not will_retry and job["job_type"] == "bg_removal":
            item_id = uuid.UUID(job["payload"]["wardrobe_item_id"])
            await wardrobe_repo.mark_needs_fix(pool, item_id, str(exc))
        elif not will_retry and job["job_type"] == "style_analysis":
            image_id = uuid.UUID(job["payload"]["inspiration_image_id"])
            await inspiration_repo.mark_failed(pool, image_id)


async def run_forever(pool: asyncpg.Pool) -> None:
    logger.info("worker started, polling every %ss", POLL_INTERVAL_SECONDS)
    while True:
        job = await jobs_repo.claim_next_job(pool)
        if job is None:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            continue
        await process_job(pool, job)


async def main() -> None:
    settings = get_settings()
    pool = await init_pool(settings.database_url)
    try:
        await run_forever(pool)
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
