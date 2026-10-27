#!/usr/bin/env python3
"""Generate the Tauri bundle icon set for the mem20controlz shell (#35).

Icons are generated rather than hand-painted so the set stays consistent and
can be reproduced from one source of truth. Run from anywhere:

    python3 src-tauri/icons/generate_icons.py

Requires Pillow. The committed rasters are the 32px tile and the 1024px master;
everything else is regenerated on demand to keep binary weight out of the tree.
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

# Output next to this script, so the caller's working directory is irrelevant.
OUT = pathlib.Path(__file__).resolve().parent

# A dark tile with three fleet bars: the accent bar is the control plane.
S = 1024
TILE = (17, 20, 24, 255)
BARS = [(94, 168, 255, 255), (86, 211, 146, 255), (140, 148, 160, 255)]


def master() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=TILE)

    bar_h = int(S * 0.115)
    gap = int(S * 0.075)
    left = int(S * 0.20)
    top = int(S * 0.28)
    for i, (width, colour) in enumerate(zip((0.60, 0.42, 0.52), BARS)):
        y = top + i * (bar_h + gap)
        d.rounded_rectangle(
            [left, y, left + int(S * width), y + bar_h],
            radius=bar_h // 2,
            fill=colour,
        )
    return img


def main() -> int:
    img = master()
    img.save(OUT / "icon.png")
    for size in (32, 128, 256, 512):
        img.resize((size, size), Image.LANCZOS).save(OUT / f"{size}x{size}.png")
    # Tauri's Linux/macOS bundlers look for the @2x variant of 128.
    (OUT / "128x128@2x.png").write_bytes((OUT / "256x256.png").read_bytes())
    print(f"wrote 6 icons into {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
