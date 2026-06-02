#!/usr/bin/env python3
"""
Merge images (JPG, PNG) and/or PDF files into a single PDF.
Usage: python merge_to_pdf.py file1.jpg file2.pdf file3.png -o output.pdf
"""

import sys
import os
import argparse
from PIL import Image
from pypdf import PdfWriter, PdfReader
import io


def safe_path(path):
    if os.path.exists(path):
        print(f"Error: '{path}' already exists. Aborting.")
        sys.exit(1)
    return path


def image_to_pdf_bytes(img_path):
    img = Image.open(img_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    buf.seek(0)
    return buf


def main():
    parser = argparse.ArgumentParser(description="Merge images/PDFs into one PDF.")
    parser.add_argument("inputs", nargs="+", help="Input files (JPG, PNG, PDF)")
    parser.add_argument("-o", "--output", default="merged.pdf", help="Output PDF path")
    args = parser.parse_args()

    safe_path(args.output)

    writer = PdfWriter()

    for f in args.inputs:
        if not os.path.exists(f):
            print(f"Error: '{f}' not found. Skipping.")
            continue

        ext = os.path.splitext(f)[1].lower()
        if ext in (".jpg", ".jpeg", ".png"):
            buf = image_to_pdf_bytes(f)
            reader = PdfReader(buf)
            for page in reader.pages:
                writer.add_page(page)
        elif ext == ".pdf":
            reader = PdfReader(f)
            for page in reader.pages:
                writer.add_page(page)
        else:
            print(f"Skipping unsupported file: {f}")

    if len(writer.pages) == 0:
        print("Error: no pages to write.")
        sys.exit(1)

    with open(args.output, "wb") as out:
        writer.write(out)

    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Saved: {args.output} ({len(writer.pages)} pages, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
