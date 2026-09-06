"""Extract a figure from a paper PDF.

Two modes:

1. Render-and-crop: render a single page of the PDF to a high-DPI image, then
   crop to a bounding box.  This is the most reliable way to grab a figure that
   includes its caption / surrounding labels exactly as printed.

       python extract_figure.py crop --pdf paper.pdf --page 5 \
           --bbox-pct 0.1,0.2,0.7,0.55 --out fig.png

   --bbox-pct is left,top,right,bottom expressed as fractions of page size
   (0,0 = top-left, 1,1 = bottom-right).  Defaults to the whole page.

2. Whole-page: render a single page as a JPEG/PNG.  Useful when the figure
   spans the whole page or you'd rather crop in another tool.

       python extract_figure.py page --pdf paper.pdf --page 5 --out p5.png

Both modes use poppler's `pdftoppm`, which is available wherever the pptx skill
runs (it's already a dependency for visual QA).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required:  pip install Pillow", file=sys.stderr)
    sys.exit(1)


def render_page(pdf_path: str, page: int, dpi: int = 220) -> Image.Image:
    """Render one page of pdf_path (1-indexed) to a PIL Image at the given DPI."""
    with tempfile.TemporaryDirectory() as td:
        prefix = os.path.join(td, "page")
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r", str(dpi),
                "-f", str(page),
                "-l", str(page),
                pdf_path,
                prefix,
            ],
            check=True,
        )
        # pdftoppm produces "<prefix>-<page>.png" (zero-padded only with -f/-l
        # ranges crossing 10/100 boundaries; here we always render exactly one
        # page, so glob for the file).
        candidates = list(Path(td).glob("page-*.png"))
        if not candidates:
            raise RuntimeError(f"pdftoppm produced no output for page {page}")
        return Image.open(candidates[0]).copy()


def crop_with_pct_bbox(img: Image.Image, bbox_pct):
    """Crop using a percent-of-page bounding box (l, t, r, b in [0,1])."""
    l, t, r, b = bbox_pct
    if not (0 <= l < r <= 1 and 0 <= t < b <= 1):
        raise ValueError(f"Invalid bbox_pct: {bbox_pct}")
    w, h = img.size
    return img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def cmd_page(args):
    img = render_page(args.pdf, args.page, dpi=args.dpi)
    img.save(args.out)
    print(f"Wrote {args.out} ({img.size[0]}x{img.size[1]} px)")


def cmd_crop(args):
    img = render_page(args.pdf, args.page, dpi=args.dpi)
    bbox = tuple(float(x) for x in args.bbox_pct.split(","))
    if len(bbox) != 4:
        raise SystemExit("--bbox-pct must be four comma-separated numbers")
    cropped = crop_with_pct_bbox(img, bbox)
    cropped.save(args.out)
    print(f"Wrote {args.out} ({cropped.size[0]}x{cropped.size[1]} px)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_page = sub.add_parser("page", help="Render whole page")
    p_page.add_argument("--pdf", required=True)
    p_page.add_argument("--page", type=int, required=True, help="1-indexed page")
    p_page.add_argument("--dpi", type=int, default=220)
    p_page.add_argument("--out", required=True)
    p_page.set_defaults(func=cmd_page)

    p_crop = sub.add_parser("crop", help="Render page then crop")
    p_crop.add_argument("--pdf", required=True)
    p_crop.add_argument("--page", type=int, required=True, help="1-indexed page")
    p_crop.add_argument("--dpi", type=int, default=220)
    p_crop.add_argument(
        "--bbox-pct", required=True,
        help="left,top,right,bottom as fractions of page (e.g., 0.1,0.2,0.7,0.55)",
    )
    p_crop.add_argument("--out", required=True)
    p_crop.set_defaults(func=cmd_crop)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
