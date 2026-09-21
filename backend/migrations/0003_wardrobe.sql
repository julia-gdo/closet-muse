CREATE TYPE clothing_category AS ENUM ('top', 'bottom', 'dress', 'shoes', 'jacket', 'accessory');
CREATE TYPE cutout_status AS ENUM ('awaiting_upload', 'pending', 'processing', 'done', 'failed', 'needs_fix');

-- Fixed style-tag vocabulary. Created here (not with inspiration images) because
-- wardrobe items need it too -- AI tags each item with these on upload so outfit
-- generation can later match items against an inspiration image's tags in code.
CREATE TABLE style_tags (
    id SMALLINT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

INSERT INTO style_tags (id, name) VALUES
    (1, 'streetwear'), (2, 'minimalist'), (3, 'boho'), (4, 'preppy'), (5, 'athleisure'),
    (6, 'classic'), (7, 'edgy'), (8, 'romantic'), (9, 'grunge'), (10, 'vintage'),
    (11, 'y2k'), (12, 'cottagecore'), (13, 'business_casual'), (14, 'formal'), (15, 'casual'),
    (16, 'coastal'), (17, 'monochrome'), (18, 'colorblock'), (19, 'utility'), (20, 'glam');

CREATE TABLE wardrobe_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category clothing_category NOT NULL,
    -- fine-grained type within the category, assigned by AI during the bg_removal
    -- job (same call that assigns style tags) -- null until that job completes
    clothing_type TEXT CHECK (clothing_type IN (
        't-shirt', 'blouse', 'sweater', 'tank', 'button-down', 'crop-top',
        'jeans', 'trousers', 'skirt', 'shorts', 'leggings',
        'mini-dress', 'midi-dress', 'maxi-dress', 'sundress',
        'sneakers', 'heels', 'boots', 'sandals', 'flats',
        'blazer', 'denim-jacket', 'coat', 'cardigan', 'hoodie',
        'bag', 'hat', 'scarf', 'belt', 'jewelry', 'sunglasses'
    )),
    original_image_key TEXT NOT NULL,
    cutout_image_key TEXT,
    cutout_status cutout_status NOT NULL DEFAULT 'awaiting_upload',
    cutout_error TEXT,
    dominant_colors TEXT[] NOT NULL DEFAULT '{}',
    label TEXT,
    is_demo_seed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_wardrobe_items_user_id ON wardrobe_items (user_id);
CREATE INDEX idx_wardrobe_items_user_category ON wardrobe_items (user_id, category);
CREATE INDEX idx_wardrobe_items_cutout_status ON wardrobe_items (cutout_status) WHERE cutout_status IN ('pending', 'processing');

CREATE TABLE wardrobe_item_tags (
    wardrobe_item_id UUID NOT NULL REFERENCES wardrobe_items(id) ON DELETE CASCADE,
    style_tag_id SMALLINT NOT NULL REFERENCES style_tags(id),
    confidence REAL,
    PRIMARY KEY (wardrobe_item_id, style_tag_id)
);
