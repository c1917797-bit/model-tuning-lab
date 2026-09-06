"""Extract a figure from a paper PDF.

Two modes:

1. Render-and-crop: render a single page of the PDF to a high-DPI image, then
   crop to a bounding box.  This is the most reliable way to grab a figure that
   includes the complete figure boundary, legend, axes and labels. Exclude page
   headers, footers, page numbers and neighboring body paragraphs.

       python extract_figure.py crop --pdf paper.pdf --page 5 --dpi 300 \
           --bbox-pct 0.1,0.2,0.7,0.55 --out fig.png

   --bbox-pct is left,top,right,bottom expressed as fractions of page size
   (0,0 = top-left, 1,1 = bottom-right).  Defaults to the whole page.

2. Whole-page: render a single page as a JPEG/PNG.  Useful when the figure
   spans the whole page or you'd rather crop in another tool.

       python extract_figure.py page --pdf paper.pdf --page 5 --dpi 300 --out p5.png

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
    from PIL import Image, ImageStat
except ImportError:
    print("Pillow is required:  pip install Pillow", file=sys.stderr)
    sys.exit(1)


def render_page(pdf_path: str, page: int, dpi: int = 300) -> Image.Image:
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


def ensure_output_quality(
    image: Image.Image,
    *,
    min_long_edge: int,
    min_short_edge: int,
) -> None:
    """阻止低分辨率或近似空白的截图进入 spec。"""
    width, height = image.size
    long_edge = max(width, height)
    short_edge = min(width, height)
    if long_edge < min_long_edge or short_edge < min_short_edge:
        raise SystemExit(
            "截图分辨率不足："
            f"{width}x{height}px；要求长边至少 {min_long_edge}px、"
            f"短边至少 {min_short_edge}px。请提高 --dpi 或扩大裁切范围。"
        )
    thumbnail = image.convert("L").resize((64, 64))
    if ImageStat.Stat(thumbnail).stddev[0] < 2.0:
        raise SystemExit("截图接近空白或对比度过低，请重新检查裁切范围。")


def cmd_page(args):
    img = render_page(args.pdf, args.page, dpi=args.dpi)
    ensure_output_quality(
        img,
        min_long_edge=args.min_long_edge,
        min_short_edge=args.min_short_edge,
    )
    img.save(args.out)
    print(
        f"Wrote {args.out} ({img.size[0]}x{img.size[1]} px). "
        "请在 100% 比例下复核图框、图例、轴标和标签完整，并确认不含相邻正文。"
    )


def cmd_crop(args):
    img = render_page(args.pdf, args.page, dpi=args.dpi)
    bbox = tuple(float(x) for x in args.bbox_pct.split(","))
    if len(bbox) != 4:
        raise SystemExit("--bbox-pct must be four comma-separated numbers")
    cropped = crop_with_pct_bbox(img, bbox)
    ensure_output_quality(
        cropped,
        min_long_edge=args.min_long_edge,
        min_short_edge=args.min_short_edge,
    )
    cropped.save(args.out)
    print(
        f"Wrote {args.out} ({cropped.size[0]}x{cropped.size[1]} px). "
        "请在 100% 比例下复核图框、图例、轴标和标签完整，并确认不含相邻正文。"
    )


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_page = sub.add_parser("page", help="Render whole page")
    p_page.add_argument("--pdf", required=True)
    p_page.add_argument("--page", type=int, required=True, help="1-indexed page")
    p_page.add_argument("--dpi", type=int, default=300)
    p_page.add_argument("--min-long-edge", type=int, default=1000)
    p_page.add_argument("--min-short-edge", type=int, default=350)
    p_page.add_argument("--out", required=True)
    p_page.set_defaults(func=cmd_page)

    p_crop = sub.add_parser("crop", help="Render page then crop")
    p_crop.add_argument("--pdf", required=True)
    p_crop.add_argument("--page", type=int, required=True, help="1-indexed page")
    p_crop.add_argument("--dpi", type=int, default=300)
    p_crop.add_argument("--min-long-edge", type=int, default=1000)
    p_crop.add_argument("--min-short-edge", type=int, default=350)
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
