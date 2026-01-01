# Docling Converter

A CLI tool for converting PDFs to high-quality Markdown, optimized for:
- **Claude AI** knowledge bases and agent sources
- **Obsidian** vaults with proper image linking
- **RAG pipelines** with chunked content

## Installation

### From GitHub
```bash
pip install git+https://github.com/antonioinnovateops/docling_converter.git
```

### From source
```bash
git clone https://github.com/antonioinnovateops/docling_converter.git
cd docling_converter
pip install -e .
```

### Build wheel
```bash
pip install build
python -m build
pip install dist/docling_converter-0.1.0-py3-none-any.whl
```

## CLI Usage

### Check version
```bash
$ docling-converter --version
docling-converter 0.1.0
```

### Basic PDF to Markdown

```bash
# Single file conversion
$ docling-converter convert INCOSE-SE-Guidebook.pdf -o output/

Converting: INCOSE-SE-Guidebook.pdf
Output dir: output
Assets dir: output/INCOSE-SE-Guidebook_assets
Processing document (this may take a while for large PDFs)...
Extracted 7 images
Markdown saved: output/INCOSE-SE-Guidebook.md

Output: output/INCOSE-SE-Guidebook.md
```

```bash
# Batch conversion - all PDFs in directory
docling-converter convert --batch /path/to/pdfs/ -o output/

# Disable OCR for faster processing (text-based PDFs only)
docling-converter convert document.pdf -o output/ --no-ocr

# Adjust image quality
docling-converter convert document.pdf -o output/ --image-scale 1.5
```

### Claude Knowledge Base

Creates chunked content optimized for RAG and Claude agents:

```bash
$ docling-converter claude INCOSE-SE-Guidebook.pdf -o knowledge/ --chunk-size 800

Converting for Claude: INCOSE-SE-Guidebook.pdf
Processing document...
Extracted 7 images
Created 210 chunks
Saved: knowledge/INCOSE-SE-Guidebook.md

Output: knowledge/INCOSE-SE-Guidebook.md
Chunks: 210
Images: 7
```

```bash
# Build knowledge base from multiple PDFs
docling-converter claude --batch /path/to/pdfs/ -o knowledge/

# Default chunk size is 1000 characters
docling-converter claude document.pdf -o knowledge/ --chunk-size 500
```

### Obsidian Vault Import

```bash
# Single file with YAML frontmatter
docling-converter obsidian document.pdf /path/to/vault/

# Batch import all PDFs
docling-converter obsidian --batch /path/to/pdfs/ /path/to/vault/

# Custom tags
docling-converter obsidian document.pdf /path/to/vault/ --tags reference aerospace

# Skip frontmatter
docling-converter obsidian document.pdf /path/to/vault/ --no-frontmatter
```

## Python API

```python
from docling_converter import (
    convert_pdf_to_markdown,
    convert_for_obsidian,
    convert_for_claude,
    build_knowledge_base,
)

# Basic conversion
md_path = convert_pdf_to_markdown("document.pdf", "output/")

# Obsidian format
md_path = convert_for_obsidian("document.pdf", "/path/to/vault/")

# Claude knowledge base with chunking
result = convert_for_claude("document.pdf", "knowledge/", chunk_size=800)
print(f"Chunks: {result['num_chunks']}")  # e.g., Chunks: 210
print(f"Images: {result['num_images']}")  # e.g., Images: 7

# Build full knowledge base from directory
kb = build_knowledge_base("pdfs/", "knowledge/")
print(f"Documents: {kb['documents']}")
```

## Output Structure

### Basic Conversion
```
output/
├── INCOSE-SE-Guidebook.md           # 208KB markdown file
└── INCOSE-SE-Guidebook_assets/      # Extracted images
    ├── image_000.png
    ├── image_001.png
    └── ... (7 images)
```

### Claude Knowledge Base
```
knowledge/
├── INDEX.md                              # Master index (batch mode)
├── INCOSE-SE-Guidebook.md                # Full markdown (208KB)
├── INCOSE-SE-Guidebook_chunks.json       # 210 RAG-ready chunks (231KB)
├── INCOSE-SE-Guidebook_metadata.json     # Document metadata
└── INCOSE-SE-Guidebook_assets/
    └── ... (7 images)
```

### Obsidian Format
```
vault/
├── document.md                      # With YAML frontmatter
├── Imported Documents Index.md      # Links to all imports
└── attachments/
    └── document/
        ├── document_img_000.png
        └── ...
```

## Features

- **OCR Support**: Extracts text from scanned documents using RapidOCR
- **Table Preservation**: Maintains table structure in markdown
- **Image Extraction**: Saves images with relative paths for portability
- **Chunking**: Splits documents for RAG/embedding pipelines
- **Obsidian Compatible**: Wiki-style links `![[image]]` and YAML frontmatter
- **Batch Processing**: Convert entire directories at once

## Command Reference

```bash
# General help
docling-converter --help

# Command-specific help
docling-converter convert --help
docling-converter obsidian --help
docling-converter claude --help
```

### Convert Options
| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory |
| `--batch` | Process all PDFs in directory |
| `--no-ocr` | Disable OCR (faster for text PDFs) |
| `--image-scale` | Image scale factor (default: 2.0) |

### Claude Options
| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory |
| `--batch` | Process all PDFs in directory |
| `--chunk-size` | Chunk size for RAG (default: 1000) |
| `--no-ocr` | Disable OCR |

### Obsidian Options
| Option | Description |
|--------|-------------|
| `--batch` | Process all PDFs in directory |
| `--tags` | Tags to add (default: imported pdf) |
| `--no-frontmatter` | Skip YAML frontmatter |
| `--no-ocr` | Disable OCR |

## Requirements

- Python >= 3.10
- docling >= 2.0.0
- docling-core >= 2.0.0

## License

MIT License
