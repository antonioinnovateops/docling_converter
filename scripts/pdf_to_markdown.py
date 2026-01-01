#!/usr/bin/env python3
"""
PDF to Markdown Converter with Image Extraction
================================================
Converts PDFs to Markdown with all artifacts (images, tables)
using relative paths - perfect for Claude knowledge bases and Obsidian vaults.

Usage:
    python pdf_to_markdown.py <input_pdf> [output_dir]
"""

import sys
import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption


def convert_pdf_to_markdown(
    pdf_path: str,
    output_dir: str = None,
    extract_images: bool = True
) -> str:
    """
    Convert a PDF to Markdown with images extracted to relative paths.

    Args:
        pdf_path: Path to the input PDF file
        output_dir: Output directory (defaults to same as PDF)
        extract_images: Whether to extract and save images

    Returns:
        Path to the generated Markdown file
    """
    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Set output directory
    if output_dir:
        output_dir = Path(output_dir).resolve()
    else:
        output_dir = pdf_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create assets folder for images (relative to output)
    doc_name = pdf_path.stem
    assets_dir = output_dir / f"{doc_name}_assets"
    assets_dir.mkdir(exist_ok=True)

    print(f"Converting: {pdf_path.name}")
    print(f"Output dir: {output_dir}")
    print(f"Assets dir: {assets_dir}")

    # Configure pipeline for best quality
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True  # Enable OCR for scanned content
    pipeline_options.do_table_structure = True  # Preserve tables
    pipeline_options.images_scale = 2.0  # Higher resolution images
    pipeline_options.generate_picture_images = True  # Extract images

    # Create converter with PDF options
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    # Convert document
    print("Processing document (this may take a while for large PDFs)...")
    result = converter.convert(str(pdf_path))

    # Export to markdown
    markdown_content = result.document.export_to_markdown()

    # Save images and update references
    image_count = 0
    if extract_images and hasattr(result.document, 'pictures'):
        for idx, picture in enumerate(result.document.pictures):
            if hasattr(picture, 'image') and picture.image is not None:
                img_filename = f"image_{idx:03d}.png"
                img_path = assets_dir / img_filename
                picture.image.pil_image.save(str(img_path))
                image_count += 1

    print(f"Extracted {image_count} images")

    # Replace <!-- image --> placeholders with actual image references
    import re
    image_placeholder_pattern = r'<!-- image -->'
    image_idx = 0

    def replace_image_placeholder(match):
        nonlocal image_idx
        img_filename = f"image_{image_idx:03d}.png"
        img_path = assets_dir / img_filename
        if img_path.exists():
            relative_path = f"{doc_name}_assets/{img_filename}"
            replacement = f"![Image {image_idx}]({relative_path})"
            image_idx += 1
            return replacement
        return match.group(0)

    markdown_content = re.sub(
        image_placeholder_pattern,
        replace_image_placeholder,
        markdown_content
    )

    # Save markdown file
    md_path = output_dir / f"{doc_name}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Markdown saved: {md_path}")

    return str(md_path)


def batch_convert(input_dir: str, output_dir: str = None) -> list:
    """
    Convert all PDFs in a directory.

    Args:
        input_dir: Directory containing PDFs
        output_dir: Output directory for all conversions

    Returns:
        List of generated Markdown file paths
    """
    input_dir = Path(input_dir)
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return []

    print(f"Found {len(pdf_files)} PDF files")
    results = []

    for pdf_file in pdf_files:
        try:
            md_path = convert_pdf_to_markdown(str(pdf_file), output_dir)
            results.append(md_path)
        except Exception as e:
            print(f"Error converting {pdf_file.name}: {e}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_markdown.py <input_pdf> [output_dir]")
        print("       python pdf_to_markdown.py --batch <input_dir> [output_dir]")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("Usage: python pdf_to_markdown.py --batch <input_dir> [output_dir]")
            sys.exit(1)
        input_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        batch_convert(input_dir, output_dir)
    else:
        pdf_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        convert_pdf_to_markdown(pdf_path, output_dir)
