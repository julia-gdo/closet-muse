-- Minimal job infra for the background-removal upload pipeline.
-- Deliberately no locked_at/locked_by/reaper query yet -- single worker,
-- add recovery machinery only if a stuck job actually becomes a problem.
CREATE TYPE job_status AS ENUM ('pending', 'processing', 'done', 'failed');

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL CHECK (job_type IN ('bg_removal')),
    status job_status NOT NULL DEFAULT 'pending',
    payload JSONB NOT NULL,
    attempts SMALLINT NOT NULL DEFAULT 0,
    max_attempts SMALLINT NOT NULL DEFAULT 3,
    last_error TEXT,
    run_after TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_jobs_poll ON jobs (status, run_after) WHERE status = 'pending';
