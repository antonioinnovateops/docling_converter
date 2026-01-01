#!/usr/bin/env python3
"""
Obsidian Vault Formatter
========================
Converts PDFs to Obsidian-compatible Markdown with:
- Wiki-style links [[note]]
- Proper image embedding ![[image.png]]
- YAML frontmatter
- Tags extraction
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption


def convert_for_obsidian(
    pdf_path: str,
    vault_path: str,
    add_frontmatter: bool = True,
    tags: list = None
) -> str:
    """
    Convert PDF to Obsidian-compatible Markdown.

    Args:
        pdf_path: Path to input PDF
        vault_path: Path to Obsidian vault root
        add_frontmatter: Add YAML frontmatter
        tags: List of tags to add

    Returns:
        Path to generated markdown file
    """
    pdf_path = Path(pdf_path).resolve()
    vault_path = Path(vault_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    vault_path.mkdir(parents=True, exist_ok=True)

    doc_name = pdf_path.stem
    # Obsidian prefers attachments folder
    attachments_dir = vault_path / "attachments" / doc_name
    attachments_dir.mkdir(parents=True, exist_ok=True)

    print(f"Converting for Obsidian: {pdf_path.name}")

    # Configure pipeline
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    print("Processing document...")
    result = converter.convert(str(pdf_path))

    # Get markdown content
    markdown_content = result.document.export_to_markdown()

    # Extract and save images with Obsidian embedding
    image_count = 0
    if hasattr(result.document, 'pictures'):
        for idx, picture in enumerate(result.document.pictures):
            if hasattr(picture, 'image') and picture.image is not None:
                img_filename = f"{doc_name}_img_{idx:03d}.png"
                img_path = attachments_dir / img_filename
                picture.image.pil_image.save(str(img_path))
                image_count += 1

                # Obsidian image embedding syntax
                obsidian_img = f"![[attachments/{doc_name}/{img_filename}]]"

                if hasattr(picture, 'self_ref'):
                    markdown_content = markdown_content.replace(
                        str(picture.self_ref),
                        obsidian_img
                    )

    print(f"Extracted {image_count} images to attachments/")

    # Convert standard markdown images to Obsidian format
    # ![alt](path) -> ![[path]]
    markdown_content = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        lambda m: f"![[{m.group(2)}]]",
        markdown_content
    )

    # Add YAML frontmatter
    if add_frontmatter:
        frontmatter = generate_frontmatter(pdf_path, tags)
        markdown_content = frontmatter + markdown_content

    # Add source reference at bottom
    markdown_content += f"\n\n---\n*Source: {pdf_path.name}*\n"

    # Save to vault
    md_path = vault_path / f"{doc_name}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Saved to vault: {md_path}")
    return str(md_path)


def generate_frontmatter(pdf_path: Path, tags: list = None) -> str:
    """Generate YAML frontmatter for Obsidian."""
    tags = tags or ["imported", "pdf"]

    frontmatter = f"""---
title: "{pdf_path.stem}"
source: "{pdf_path.name}"
created: {datetime.now().strftime("%Y-%m-%d")}
tags: {tags}
type: reference
---

"""
    return frontmatter


def batch_import_to_vault(pdf_folder: str, vault_path: str, tags: list = None):
    """Import all PDFs from a folder to Obsidian vault."""
    pdf_folder = Path(pdf_folder)
    pdf_files = list(pdf_folder.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDFs found in {pdf_folder}")
        return []

    print(f"Importing {len(pdf_files)} PDFs to Obsidian vault...")
    results = []

    for pdf_file in pdf_files:
        try:
            md_path = convert_for_obsidian(
                str(pdf_file),
                vault_path,
                tags=tags
            )
            results.append(md_path)
        except Exception as e:
            print(f"Error importing {pdf_file.name}: {e}")

    # Create index note
    create_index_note(vault_path, results)
    return results


def create_index_note(vault_path: str, imported_files: list):
    """Create an index note linking all imported documents."""
    vault_path = Path(vault_path)

    index_content = """---
title: "Imported Documents Index"
created: {date}
tags: [index, moc]
---

# Imported Documents

This note links to all imported PDF documents.

## Documents

""".format(date=datetime.now().strftime("%Y-%m-%d"))

    for file_path in imported_files:
        name = Path(file_path).stem
        index_content += f"- [[{name}]]\n"

    index_path = vault_path / "Imported Documents Index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    print(f"Created index: {index_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python obsidian_formatter.py <pdf_path> <vault_path>")
        print("       python obsidian_formatter.py --batch <pdf_folder> <vault_path>")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        batch_import_to_vault(sys.argv[2], sys.argv[3])
    else:
        convert_for_obsidian(sys.argv[1], sys.argv[2])
