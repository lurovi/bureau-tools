#!/usr/bin/env python3
"""
Resize an image, reduce DPI, and optionally convert format.
Usage: python img_compress.py input.jpg [--scale 70] [--dpi 96] [--format jpeg]
"""

import sys
import os
import argparse
from PIL import Image


def safe_output_path(base, ext):
    path = f"{base}.{ext}"
    if os.path.exists(path):
        print(f"Error: output file '{path}' already exists. Aborting.")
        sys.exit(1)
    return path


def main():
    parser = argparse.ArgumentParser(description="Compress/resize an image.")
    parser.add_argument("input", help="Input image (JPG, JPEG, PNG)")
    parser.add_argument("--scale", type=float, default=70, help="Scale percentage (default: 70)")
    parser.add_argument("--dpi", type=int, default=96, help="Output DPI (default: 96)")
    parser.add_argument("--format", choices=["jpeg", "png"], default=None,
                        help="Output format (default: same as input)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    ext_in = os.path.splitext(args.input)[1].lower().lstrip(".")
    if ext_in not in ("jpg", "jpeg", "png"):
        print("Error: input must be JPG, JPEG, or PNG.")
        sys.exit(1)

    out_fmt = args.format or ("jpeg" if ext_in in ("jpg", "jpeg") else "png")
    out_ext = "jpg" if out_fmt == "jpeg" else "png"
    base_name = os.path.splitext(args.input)[0] + "_compressed"
    out_path = safe_output_path(base_name, out_ext)

    img = Image.open(args.input)
    if img.mode in ("RGBA", "P") and out_fmt == "jpeg":
        img = img.convert("RGB")

    new_w = int(img.width * args.scale / 100)
    new_h = int(img.height * args.scale / 100)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    save_kwargs = {"dpi": (args.dpi, args.dpi)}
    if out_fmt == "jpeg":
        save_kwargs["quality"] = 85
        save_kwargs["optimize"] = True

    img.save(out_path, format=out_fmt.upper(), **save_kwargs)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Saved: {out_path} ({new_w}x{new_h}, {args.dpi} DPI, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
