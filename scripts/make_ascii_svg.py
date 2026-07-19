from __future__ import annotations

import html
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np


# Extended 70-char ramp for much finer tonal gradation.
# Ordered from lightest (space) to darkest (@).
RAMP = " `.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"

SOURCE = Path("images/source-prepped.png")
OUTPUT = Path("avi-ascii.svg")


def grayscale_to_ascii(pixel: int) -> str:
    """Map a 0-255 grayscale value to an ASCII character."""
    normalized = max(0, min(255, pixel)) / 255.0
    index = int(normalized * (len(RAMP) - 1))
    return RAMP[index]


def enhance_image(img: Image.Image) -> Image.Image:
    """Apply multi-stage enhancement to bring out facial features."""
    # 1. Auto-contrast to use full dynamic range
    img = ImageOps.autocontrast(img, cutoff=1)

    # 2. Boost contrast to make dark features (eyes, eyebrows, nostrils,
    #    mouth line, hair) stand out more against skin tones
    img = ImageEnhance.Contrast(img).enhance(1.4)

    # 3. Slight brightness reduction so mid-tones map to richer characters
    img = ImageEnhance.Brightness(img).enhance(0.95)

    # 4. Unsharp mask — the key for crisp edges on eyes/nose/mouth.
    #    radius=2 targets fine facial detail, percent=150 is aggressive
    #    but won't over-sharpen at our target resolution, threshold=3
    #    prevents noise amplification on flat skin areas.
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    return img


def build_ascii_art(image_path: Path, width: int = 100) -> list[str]:
    """Convert an image to ASCII rows.

    Using width=100 (up from 76) gives ~30% more horizontal resolution,
    which is critical for small features like pupils and nostrils.
    """
    with Image.open(image_path) as img:
        original = img.convert("L")

        # Enhancement pipeline
        original = enhance_image(original)

        # Character cells are roughly 2x tall as wide in monospace fonts.
        # 0.5 compensates for this; we use 0.52 to slightly stretch the
        # face vertically which helps definition on eyes and mouth.
        aspect = max(1, int(round(original.height * width / original.width * 0.52)))
        resized = original.resize((width, aspect), Image.Resampling.LANCZOS)

    pixels = np.array(resized)
    rows: list[str] = []
    for y in range(pixels.shape[0]):
        row_chars = []
        for x in range(pixels.shape[1]):
            row_chars.append(grayscale_to_ascii(int(pixels[y, x])))
        rows.append("".join(row_chars))
    return rows


def xml_escape(text: str) -> str:
    """Escape special XML characters so the SVG is well-formed."""
    return html.escape(text, quote=False)


def build_svg(rows: list[str]) -> str:
    char_width = 6.02        # tighter kerning for denser portrait
    char_height = 9.6        # slightly tighter line spacing
    pad_x = 20
    pad_top = 44
    pad_bottom = 20
    width = int(len(rows[0]) * char_width + pad_x * 2)
    height = int(len(rows) * char_height + pad_top + pad_bottom)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect width="100%" height="100%" fill="#0d1117" rx="6"/>',
        f'<text x="{pad_x}" y="28" font-family="Consolas, \'Courier New\', monospace" font-size="14" fill="#e6edf3">ASCII Portrait</text>',
    ]

    font_size = char_height
    for row_index, row in enumerate(rows):
        y = pad_top + row_index * char_height
        escaped_row = xml_escape(row)
        delay = round(row_index * 0.035, 4)
        parts.append(
            f'<g opacity="0" transform="translate(0 8) scale(0.88)">'
            f'<text x="{pad_x}" y="{y}" font-family="Consolas, \'Courier New\', monospace" font-size="{font_size}" fill="#8b949e" xml:space="preserve">{escaped_row}</text>'
            f'<animate attributeName="opacity" values="0;1" dur="0.24s" begin="{delay}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 8;0 0" dur="0.24s" begin="{delay}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="scale" values="0.88 0.88;1 1" dur="0.24s" begin="{delay}s" fill="freeze" additive="sum"/>'
            '</g>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing source image: {SOURCE}")
        return 1

    rows = build_ascii_art(SOURCE)
    print(f"Generated {len(rows)} rows × {len(rows[0])} cols ASCII art")
    OUTPUT.write_text(build_svg(rows), encoding="utf-8")
    print(f"Saved {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
