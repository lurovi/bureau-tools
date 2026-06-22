#!/usr/bin/env python3
"""
Make a PDF look like it was printed, signed by hand, and scanned.
Applies rotation, blur, noise, brightness/contrast tweaks, and a slight yellowing.
Usage: python pdf_scanify.py input.pdf [--dpi 150] [--rotate 1.8] [--noise 8]
"""

import sys
import os
import argparse
import random
import io
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from pdf2image import convert_from_path
import img2pdf


def safe_path(path):
    if os.path.exists(path):
        print(f"Error: '{path}' already exists. Aborting.")
        sys.exit(1)
    return path


def apply_scan_effect(img, rotate_deg, noise_level):
    # slight rotation to simulate misaligned scan
    angle = random.uniform(-abs(rotate_deg), abs(rotate_deg))
    img = img.rotate(angle, expand=False, fillcolor=(255, 250, 210), resample=Image.BICUBIC)

    # convert to numpy for noise and color tweaks
    arr = np.array(img, dtype=np.float32)

    # add gaussian noise
    noise = np.random.normal(0, noise_level, arr.shape)
    arr = np.clip(arr + noise, 0, 255)

    # yellowing: boost red/green, reduce blue
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.025, 0, 255)  # red
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.015, 0, 255)  # green
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.96, 0, 255)   # blue

    img = Image.fromarray(arr.astype(np.uint8))

    # slight blur to simulate scan softness
    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.7)))

    # small brightness/contrast variation
    img = ImageEnhance.Brightness(img).enhance(random.uniform(0.93, 1.02))
    img = ImageEnhance.Contrast(img).enhance(random.uniform(0.90, 1.05))

    return img


def main():
    parser = argparse.ArgumentParser(description="Scanify a PDF.")
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("--dpi", type=int, default=150, help="Render DPI (default: 150)")
    parser.add_argument("--rotate", type=float, default=1.8,
                        help="Max random rotation degrees (default: 1.8)")
    parser.add_argument("--noise", type=float, default=7,
                        help="Gaussian noise std dev (default: 7)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    out_path = safe_path(os.path.splitext(args.input)[0] + "_scanned.pdf")

    print(f"Rendering pages at {args.dpi} DPI...")
    pages = convert_from_path(args.input, dpi=args.dpi)

    processed = []
    for i, page in enumerate(pages):
        print(f"  Processing page {i + 1}/{len(pages)}...")
        page = page.convert("RGB")
        page = apply_scan_effect(page, args.rotate, args.noise)
        buf = io.BytesIO()
        page.save(buf, format="JPEG", quality=88, optimize=True)
        buf.seek(0)
        processed.append(buf.read())

    with open(out_path, "wb") as f:
        f.write(img2pdf.convert(processed))

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Saved: {out_path} ({len(pages)} pages, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
