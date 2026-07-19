from pathlib import Path
import sys

from PIL import Image
import cv2
import numpy as np
from rembg import remove


OUTPUT = Path("images/source-prepped.png")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <image>")
        return 1

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Image not found: {input_path}")
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as source:
        rgba = source.convert("RGBA")

    removed = remove(rgba)
    white_bg = Image.new("RGBA", removed.size, (255, 255, 255, 255))
    white_bg.paste(removed, mask=removed.getchannel("A"))

    gray = cv2.cvtColor(np.array(white_bg), cv2.COLOR_RGBA2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    Image.fromarray(gray).save(OUTPUT)
    print(f"Saved {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
