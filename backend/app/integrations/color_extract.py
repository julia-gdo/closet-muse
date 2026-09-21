import io

from PIL import Image


def extract_dominant_colors(image_bytes: bytes, max_colors: int = 3) -> list[str]:
    """Dominant colors as hex strings, ignoring transparent pixels. Deterministic
    color math, not AI -- cheaper and more reliable for this than a model call."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img.thumbnail((150, 150))

    opaque_pixels = [(r, g, b) for r, g, b, a in img.getdata() if a > 128]
    if not opaque_pixels:
        return []

    sample = Image.new("RGB", (len(opaque_pixels), 1))
    sample.putdata(opaque_pixels)
    quantized = sample.quantize(colors=max_colors, method=Image.MEDIANCUT)
    palette = quantized.getpalette() or []

    color_counts = sorted(quantized.getcolors() or [], key=lambda c: c[0], reverse=True)

    hex_colors = []
    for _count, palette_index in color_counts[:max_colors]:
        r, g, b = palette[palette_index * 3 : palette_index * 3 + 3]
        hex_colors.append(f"#{r:02x}{g:02x}{b:02x}")
    return hex_colors
