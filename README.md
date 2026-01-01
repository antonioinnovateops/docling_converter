# Docling Converter

A CLI tool for converting PDFs to high-quality Markdown, optimized for:
- **Claude AI** knowledge bases and agent sources
- **Obsidian** vaults with proper image linking
- **RAG pipelines** with chunked content

## Installation

### From PyPI (when published)
```bash
pip install docling-converter
```

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

### Basic PDF to Markdown

```bash
# Single file
docling-converter convert document.pdf -o output/

# Batch conversion
docling-converter convert --batch /path/to/pdfs/ -o output/

# With options
docling-converter convert document.pdf -o output/ --no-ocr --image-scale 1.5
```

### Obsidian Vault Import

```bash
# Single file
docling-converter obsidian document.pdf /path/to/vault/

# Batch import
docling-converter obsidian --batch /path/to/pdfs/ /path/to/vault/

# With custom tags
docling-converter obsidian document.pdf /path/to/vault/ --tags reference technical
```

### Claude Knowledge Base

```bash
# Single file with chunking
docling-converter claude document.pdf -o knowledge/

# Batch build knowledge base
docling-converter claude --batch /path/to/pdfs/ -o knowledge/

# Custom chunk size
docling-converter claude document.pdf -o knowledge/ --chunk-size 500
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

# Claude knowledge base
result = convert_for_claude("document.pdf", "knowledge/")
print(f"Chunks: {result['num_chunks']}")

# Build full knowledge base
kb = build_knowledge_base("pdfs/", "knowledge/")
print(f"Documents: {kb['documents']}")
```

## Output Structure

### Basic Conversion
```
output/
├── document.md                # Markdown file
└── document_assets/           # Images folder
    ├── image_000.png
    ├── image_001.png
    └── ...
```

### Obsidian Format
```
vault/
├── document.md                # With YAML frontmatter
├── Imported Documents Index.md
└── attachments/
    └── document/
        ├── document_img_000.png
        └── ...
```

### Claude Knowledge Base
```
knowledge/
├── INDEX.md                   # Master index
├── document.md                # Full markdown
├── document_chunks.json       # RAG-ready chunks
├── document_metadata.json     # Document metadata
└── document_assets/
    └── ...
```

## Features

- **OCR Support**: Extracts text from scanned documents
- **Table Preservation**: Maintains table structure in markdown
- **Image Extraction**: Saves images with relative paths
- **Chunking**: Splits documents for RAG/embedding pipelines
- **Obsidian Compatible**: Wiki-style links and frontmatter
- **Batch Processing**: Convert entire directories

## Command Reference

```
docling-converter --help
docling-converter convert --help
docling-converter obsidian --help
docling-converter claude --help
```

## License

MIT License
