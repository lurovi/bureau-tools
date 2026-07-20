# bureau-tools

A small collection of local Python scripts for avoiding the print→sign→scan bureaucracy loop.
No data ever leaves your machine.

## Installation

### Option 1: Using pixi (Recommended) 🚀

[Pixi](https://pixi.sh) handles all dependencies including system packages (poppler, ghostscript) automatically:

```bash
# Install pixi if you don't have it
curl -fsSL https://pixi.sh/install.sh | bash

# Source bashrc to apply effects to current shell directly
source ~/.bashrc 

# Install all dependencies
pixi install

# Run any script
pixi run pdf-editor
pixi run img-compress scan.png --scale 60
pixi run pdf-scanify document.pdf
```

### Option 2: Using pip

```bash
pip install -r requirements.txt
```

**Additional system dependencies:**

For `pdf_compress.py` you need **Ghostscript**:
- Linux: `sudo apt install ghostscript`
- macOS: `brew install ghostscript`
- Windows: download from https://www.ghostscript.com

For `pdf_scanify.py`, `merge_to_pdf.py`, and `pdf_editor.py` you need **poppler**:
- Linux: `sudo apt install poppler-utils`
- macOS: `brew install poppler`
- Windows: download from https://github.com/oschwartz10612/poppler-windows/releases

---

## Scripts

### `pdf_editor.py` — Interactive PDF Editor

A GUI application for adding text and images (including transparent signatures) directly to PDFs.

```bash
# With pixi
pixi run pdf-editor [input.pdf]

# With python
python src/pdf_editor.py [input.pdf]
```

**Features:**
- ✍️ Add text anywhere with customizable color and font size
- 🖼️ Insert images with transparency support (perfect for signatures)
- ↔️ Move and resize text/images interactively
- 🗑️ Delete annotations (Delete/Backspace key)
- 🔍 Zoom controls for precise positioning
- 💾 Save without overwriting existing files

**Workflow:**
1. Open a PDF or pass it as a command-line argument
2. Select "Text Color" to choose your text color
3. Switch between modes:
   - **Add Text**: Click anywhere to add text
   - **Insert Image**: Select your signature image, then click to place it
   - **Edit/Move**: Click to select, drag to move, use handles to resize images
4. Use Delete/Backspace to remove selected annotations
5. Save with a unique filename (prevents accidental overwrites)

**Tips:**
- Use PNG images with transparent backgrounds for signatures (created with GIMP, etc.)
- In Edit/Move mode, click on images to see resize handles at corners and edges
- Zoom in for precise placement, zoom out for overview

If the PDF file is large, it can take a bit to save it, just wait, at some point the PDF will appear and a successfull dialog will appear as well.

---

### `img_compress.py` — Resize & compress an image

Reduces resolution by a percentage, lowers DPI, and optionally converts format.

```bash
# With pixi
pixi run img-compress scan.png --scale 60 --dpi 96 --format jpeg

# With python
python src/img_compress.py scan.png --scale 60 --dpi 96 --format jpeg
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
# With pixi
pixi run merge-to-pdf page1.jpg page2.png attachment.pdf -o final.pdf

# With python
python src/merge_to_pdf.py page1.jpg page2.png attachment.pdf -o final.pdf
```

| Flag | Default | Description |
|------|---------|-------------|
| `-o` | merged.pdf | Output file path |

---

### `pdf_compress.py` — Shrink a PDF

Uses Ghostscript to reduce file size.

```bash
# With pixi
pixi run pdf-compress input.pdf --dpi 120 --quality 75

# With python
python src/pdf_compress.py input.pdf --dpi 120 --quality 75
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
# With pixi
pixi run pdf-scanify signed_form.pdf --dpi 150 --rotate 1.8 --noise 7

# With python
python src/pdf_scanify.py signed_form.pdf --dpi 150 --rotate 1.8 --noise 7
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
