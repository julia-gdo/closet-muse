from typing import Any

import asyncpg

RETRY_DELAY_SECONDS = 30


async def enqueue_job(conn: asyncpg.Connection, job_type: str, payload: dict[str, Any]) -> str:
    row = await conn.fetchrow(
        "INSERT INTO jobs (job_type, payload) VALUES ($1, $2) RETURNING id",
        job_type,
        payload,
    )
    return str(row["id"])


async def claim_next_job(pool: asyncpg.Pool) -> asyncpg.Record | None:
    # Single atomic UPDATE ... RETURNING (rather than SELECT then UPDATE) so the
    # returned row reflects the post-increment attempts count, not a stale value.
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            UPDATE jobs
            SET status = 'processing', attempts = attempts + 1, updated_at = now()
            WHERE id = (
                SELECT id FROM jobs
                WHERE status = 'pending' AND run_after <= now()
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING *
            """
        )


async def mark_job_done(pool: asyncpg.Pool, job_id) -> None:
    await pool.execute(
        "UPDATE jobs SET status = 'done', updated_at = now() WHERE id = $1", job_id
    )


async def mark_job_failed_or_retry(pool: asyncpg.Pool, job_id, attempts: int, max_attempts: int, error: str) -> bool:
    """Returns True if the job will retry, False if it's terminally failed."""
    if attempts < max_attempts:
        await pool.execute(
            """
            UPDATE jobs
            SET status = 'pending', last_error = $2, run_after = now() + make_interval(secs => $3), updated_at = now()
            WHERE id = $1
            """,
            job_id,
            error,
            RETRY_DELAY_SECONDS,
        )
        return True
    await pool.execute(
        "UPDATE jobs SET status = 'failed', last_error = $2, updated_at = now() WHERE id = $1",
        job_id,
        error,
    )
    return False
