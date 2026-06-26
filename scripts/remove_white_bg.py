#!/usr/bin/env python3
"""
Remove white backgrounds from boat JPGs and save as transparent PNGs.

Strategy:
1. Build a luminance mask (255 where pixel is bright/near-white).
2. Flood-fill from edge pixels — only the CONNECTED white region (the
   actual background) gets marked. White interior to the boat (seats,
   railings, hull paint) is preserved.
3. Convert the marked region to alpha=0; lightly feather the edges.

Re-run if you re-export from Photoshop. Reads NO Background boat photots/*.jpg
and writes the matching *.png alongside.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

THRESHOLD = 232      # pixels with luminance >= this are background candidates
FEATHER   = 1.0      # gaussian-blur radius on the alpha mask (px)

def remove_white(input_path: Path, output_path: Path) -> None:
    img = Image.open(input_path).convert("RGB")
    w, h = img.size

    gray = img.convert("L")
    bright = gray.point(lambda v: 255 if v >= THRESHOLD else 0).convert("L")

    flood = bright.copy()
    # Seed the flood-fill from every edge pixel that's bright. floodfill is
    # idempotent on already-marked pixels, so multiple seeds are cheap.
    for y in range(h):
        for x in (0, w - 1):
            if flood.getpixel((x, y)) == 255:
                ImageDraw.floodfill(flood, (x, y), 128)
    for x in range(w):
        for y in (0, h - 1):
            if flood.getpixel((x, y)) == 255:
                ImageDraw.floodfill(flood, (x, y), 128)

    alpha = flood.point(lambda v: 0 if v == 128 else 255).convert("L")
    if FEATHER > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=FEATHER))

    result = img.convert("RGBA")
    result.putalpha(alpha)
    result.save(output_path, "PNG", optimize=True)
    size_kb = output_path.stat().st_size // 1024
    print(f"  {input_path.name:32s} -> {output_path.name:32s} ({size_kb} KB)")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    folder = repo_root / "NO Background boat photots"
    jpgs = sorted(folder.glob("*.jpg"))
    if not jpgs:
        print(f"No JPGs found in {folder}")
        return
    print(f"Converting {len(jpgs)} files in {folder.name}/")
    for jpg in jpgs:
        png = jpg.with_suffix(".png")
        remove_white(jpg, png)
    print("Done.")


if __name__ == "__main__":
    main()
