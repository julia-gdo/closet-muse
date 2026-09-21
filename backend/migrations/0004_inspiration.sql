ALTER TABLE jobs DROP CONSTRAINT jobs_job_type_check;
ALTER TABLE jobs ADD CONSTRAINT jobs_job_type_check CHECK (job_type IN ('bg_removal', 'style_analysis'));

CREATE TYPE analysis_status AS ENUM ('awaiting_upload', 'pending', 'processing', 'done', 'failed');

-- style_tags already exists (created in 0003_wardrobe.sql, shared with wardrobe items)
CREATE TABLE inspiration_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_key TEXT NOT NULL,
    analysis_status analysis_status NOT NULL DEFAULT 'awaiting_upload',
    summary TEXT,
    dominant_colors TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_inspiration_images_user_id ON inspiration_images (user_id);

CREATE TABLE inspiration_image_tags (
    inspiration_image_id UUID NOT NULL REFERENCES inspiration_images(id) ON DELETE CASCADE,
    style_tag_id SMALLINT NOT NULL REFERENCES style_tags(id),
    confidence REAL,
    PRIMARY KEY (inspiration_image_id, style_tag_id)
);
