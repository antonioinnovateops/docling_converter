"""
Docling Converter - PDF to Markdown conversion for Claude & Obsidian

A CLI tool for converting PDFs to high-quality Markdown with:
- Image extraction with relative paths
- Obsidian vault formatting
- Claude knowledge base building with chunking for RAG
"""

__version__ = "0.1.0"
__author__ = "Antonio InnovateOps"

from .converter import convert_pdf_to_markdown, batch_convert
from .obsidian import convert_for_obsidian, batch_import_to_vault
from .knowledge import convert_for_claude, build_knowledge_base

__all__ = [
    "convert_pdf_to_markdown",
    "batch_convert",
    "convert_for_obsidian",
    "batch_import_to_vault",
    "convert_for_claude",
    "build_knowledge_base",
]
