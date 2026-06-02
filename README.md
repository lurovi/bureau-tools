# bureau-tools

A small collection of local Python scripts for avoiding the print→sign→scan bureaucracy loop.
No data ever leaves your machine.

## Requirements

```
pip install Pillow pypdf pdf2image img2pdf numpy
```

For `pdf_compress.py` you also need **Ghostscript**:
- Linux: `sudo apt install ghostscript`
- macOS: `brew install ghostscript`
- Windows: download from https://www.ghostscript.com

For `pdf_scanify.py` and `merge_to_pdf.py` with images, `pdf2image` requires **poppler**:
- Linux: `sudo apt install poppler-utils`
- macOS: `brew install poppler`
- Windows: download from https://github.com/oschwartz10612/poppler-windows/releases

---

## Scripts

### `img_compress.py` — Resize & compress an image

Reduces resolution by a percentage, lowers DPI, and optionally converts format.

```bash
python img_compress.py scan.png --scale 60 --dpi 96 --format jpeg
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scale` | 70 | Resize to this % of original dimensions |
| `--dpi` | 96 | Output DPI |
| `--format` | same | `jpeg` or `png` |

Output: `<input>_compressed.jpg` (or `.png`)

---

### `merge_to_pdf.py` — Combine images/PDFs into one PDF

Accepts any mix of JPG, PNG, and PDF files in the order you list them.

```bash
python merge_to_pdf.py page1.jpg page2.png attachment.pdf -o final.pdf
```

| Flag | Default | Description |
|------|---------|-------------|
| `-o` | merged.pdf | Output file path |

---

### `pdf_compress.py` — Shrink a PDF

Uses Ghostscript to reduce file size.

```bash
python pdf_compress.py input.pdf --dpi 120 --quality 75
```

| Flag | Default | Description |
|---------|-----|----------|
| `--dpi` | 120 | render resolution (lower = smaller file, less detail) |
| `--quality` | 75 | JPEG compression 1-95 (lower = smaller file, more artifacts) |

Output: `<input>_compressed.pdf`

---

### `pdf_scanify.py` — Make a PDF look scanned

Applies slight rotation, gaussian noise, blur, brightness/contrast variation, and paper yellowing so a cleanly-filled PDF looks like it was printed, signed by hand, and fed through a scanner.

```bash
python pdf_scanify.py signed_form.pdf --dpi 150 --rotate 1.8 --noise 7
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dpi` | 150 | Render resolution (higher = better quality but slower) |
| `--rotate` | 1.8 | Max random rotation ±degrees per page |
| `--noise` | 7 | Gaussian noise intensity |

Output: `<input>_scanned.pdf`

---

## Safety

All scripts abort with an error if the output file already exists — no silent overwrites.
