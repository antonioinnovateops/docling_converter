# Docling Tutorials - PDF to Markdown for Claude & Obsidian

This folder contains scripts and tutorials for converting PDFs to high-quality Markdown documents, optimized for:
- **Claude AI** knowledge bases and agent sources
- **Obsidian** vaults with proper image linking
- **RAG pipelines** and document processing

## Installation

```bash
pip install docling docling-core
```

## Quick Start

### Single PDF Conversion
```bash
python scripts/pdf_to_markdown.py /path/to/document.pdf
```

### Batch Conversion
```bash
python scripts/pdf_to_markdown.py --batch /path/to/pdf_folder /path/to/output
```

## Folder Structure

```
docling_tutorials/
├── scripts/           # Conversion scripts
│   ├── pdf_to_markdown.py      # Main converter
│   ├── obsidian_formatter.py   # Obsidian-specific formatting
│   └── claude_knowledge.py     # Claude knowledge base builder
├── examples/          # Example notebooks and scripts
├── output/            # Converted documents go here
└── assets/            # Shared assets
```

## Output Structure

Each converted PDF creates:
```
output/
├── document_name.md              # Main markdown file
└── document_name_assets/         # Folder with images
    ├── image_000.png
    ├── image_001.png
    └── ...
```

Images use **relative paths** so the folder is portable.

## Use Cases

### 1. Claude Knowledge Base
Convert technical documentation for Claude agents:
```python
from scripts.claude_knowledge import build_knowledge_base

build_knowledge_base(
    pdf_folder="/path/to/docs",
    output_folder="/path/to/knowledge"
)
```

### 2. Obsidian Vault
Import PDFs into Obsidian with proper linking:
```python
from scripts.obsidian_formatter import convert_for_obsidian

convert_for_obsidian(
    pdf_path="/path/to/doc.pdf",
    vault_path="/path/to/obsidian/vault"
)
```

### 3. RAG Pipeline
Process documents for retrieval-augmented generation:
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("document.pdf")

# Get chunks for embedding
chunks = result.document.export_to_markdown().split("\n\n")
```

## Features

- **OCR Support**: Extracts text from scanned documents
- **Table Preservation**: Maintains table structure in markdown
- **Image Extraction**: Saves images with relative paths
- **Formula Support**: Converts LaTeX formulas
- **Metadata Extraction**: Captures document metadata

## Tips for Best Results

1. **High-quality PDFs**: Vector PDFs convert better than scanned images
2. **Enable OCR**: For scanned documents, OCR is automatic
3. **Check images**: Some complex diagrams may need manual review
4. **Tables**: Complex merged cells may need cleanup

## Troubleshooting

### Memory Issues
For large PDFs (>100 pages), process in batches:
```python
pipeline_options.images_scale = 1.0  # Lower for memory
```

### Missing Images
Ensure `generate_picture_images = True` in pipeline options.

### OCR Quality
For better OCR, install Tesseract:
```bash
apt-get install tesseract-ocr
```
