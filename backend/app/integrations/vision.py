import json

from google import genai
from google.genai import types

from app.core.config import get_settings

MODEL = "gemini-3.6-flash"

CLOTHING_TYPES_BY_CATEGORY: dict[str, list[str]] = {
    "top": ["t-shirt", "blouse", "sweater", "tank", "button-down", "crop-top"],
    "bottom": ["jeans", "trousers", "skirt", "shorts", "leggings"],
    "dress": ["mini-dress", "midi-dress", "maxi-dress", "sundress"],
    "shoes": ["sneakers", "heels", "boots", "sandals", "flats"],
    "jacket": ["blazer", "denim-jacket", "coat", "cardigan", "hoodie"],
    "accessory": ["bag", "hat", "scarf", "belt", "jewelry", "sunglasses"],
}

STYLE_TAGS = [
    "streetwear", "minimalist", "boho", "preppy", "athleisure",
    "classic", "edgy", "romantic", "grunge", "vintage",
    "y2k", "cottagecore", "business_casual", "formal", "casual",
    "coastal", "monochrome", "colorblock", "utility", "glam",
]

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        # Explicit timeout so a transient upstream error (e.g. 503 "high demand")
        # fails fast into our own job-level retry (30s backoff) instead of the
        # SDK's internal retry silently hanging for minutes.
        _client = genai.Client(
            api_key=get_settings().gemini_api_key,
            http_options=types.HttpOptions(timeout=45_000),
        )
    return _client


async def tag_wardrobe_item(image_bytes: bytes, category: str) -> dict:
    """Single constrained vision call: picks one clothing_type valid for the
    item's category, and 1-2 style tags from the fixed vocabulary. Response is
    validated against both fixed lists -- anything hallucinated outside them
    is dropped rather than trusted."""
    valid_types = CLOTHING_TYPES_BY_CATEGORY[category]

    prompt = (
        f"This is a photo of a clothing item in the category '{category}'. "
        f"Pick exactly one clothing_type from this list that best matches: {valid_types}. "
        f"Also pick 1 or 2 style_tags from this list that best describe its aesthetic: {STYLE_TAGS}. "
        'Respond with JSON only, in this exact shape: {"clothing_type": "...", "style_tags": ["...", "..."]}'
    )

    response = await _get_client().aio.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        parsed = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return {"clothing_type": None, "style_tags": []}

    clothing_type = parsed.get("clothing_type")
    if clothing_type not in valid_types:
        clothing_type = None

    raw_tags = parsed.get("style_tags") or []
    style_tags = [tag for tag in raw_tags if tag in STYLE_TAGS][:2]

    return {"clothing_type": clothing_type, "style_tags": style_tags}


async def analyze_inspiration_image(image_bytes: bytes) -> dict:
    """Single constrained vision call: 1-5 style tags from the fixed vocabulary
    plus a short summary. Dominant colors are deliberately NOT asked of the model
    here -- color_extract.py's deterministic Pillow-based extraction is cheaper
    and more reliable than trusting a vision model's color perception."""
    prompt = (
        "This is a fashion/style inspiration image. Pick 1 to 5 style_tags from this list that best "
        f"describe its aesthetic: {STYLE_TAGS}. Also write a short summary (one sentence, under 200 "
        "characters) describing the overall look. "
        'Respond with JSON only, in this exact shape: {"style_tags": ["...", "..."], "summary": "..."}'
    )

    response = await _get_client().aio.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        parsed = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return {"style_tags": [], "summary": None}

    raw_tags = parsed.get("style_tags") or []
    style_tags = [tag for tag in raw_tags if tag in STYLE_TAGS][:5]

    summary = parsed.get("summary")
    if not isinstance(summary, str):
        summary = None
    elif len(summary) > 200:
        summary = summary[:200]

    return {"style_tags": style_tags, "summary": summary}
