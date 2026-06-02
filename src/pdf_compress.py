#!/usr/bin/env python3
"""
Reduce PDF file size by re-rendering pages as compressed JPEG images.
Usage: python pdf_compress.py input.pdf [--dpi 120] [--quality 75]

--dpi     render resolution (lower = smaller file, less detail)
--quality JPEG compression 1-95 (lower = smaller file, more artifacts)
"""

import sys
import os
import io
import argparse
from PIL import Image
from pdf2image import convert_from_path
import img2pdf


def safe_path(path):
    if os.path.exists(path):
        print(f"Error: '{path}' already exists. Aborting.")
        sys.exit(1)
    return path


def main():
    parser = argparse.ArgumentParser(description="Compress a PDF by re-rendering its pages.")
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("--dpi", type=int, default=120,
                        help="Render DPI (default: 120). Lower = smaller file.")
    parser.add_argument("--quality", type=int, default=75,
                        help="JPEG quality 1-95 (default: 75). Lower = smaller file.")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    if not (1 <= args.quality <= 95):
        print("Error: --quality must be between 1 and 95.")
        sys.exit(1)

    out_path = safe_path(os.path.splitext(args.input)[0] + "_compressed.pdf")

    print(f"Rendering at {args.dpi} DPI, JPEG quality {args.quality}...")
    pages = convert_from_path(args.input, dpi=args.dpi)

    buffers = []
    for i, page in enumerate(pages):
        print(f"  Page {i + 1}/{len(pages)}")
        buf = io.BytesIO()
        page.convert("RGB").save(buf, format="JPEG", quality=args.quality, optimize=True)
        buf.seek(0)
        buffers.append(buf.read())

    with open(out_path, "wb") as f:
        f.write(img2pdf.convert(buffers))

    orig_mb = os.path.getsize(args.input) / (1024 * 1024)
    new_mb = os.path.getsize(out_path) / (1024 * 1024)
    ratio = (1 - new_mb / orig_mb) * 100 if orig_mb > 0 else 0
    print(f"Saved: {out_path}")
    print(f"  {orig_mb:.2f} MB -> {new_mb:.2f} MB ({ratio:.1f}% reduction)")


if __name__ == "__main__":
    main()
