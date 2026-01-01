"""
Claude knowledge base builder module.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption


def convert_for_claude(
    pdf_path: str,
    output_dir: str,
    chunk_size: int = 1000,
    ocr: bool = True,
) -> Dict[str, Any]:
    """
    Convert PDF to Claude-optimized knowledge format.

    Args:
        pdf_path: Path to input PDF
        output_dir: Output directory
        chunk_size: Approximate chunk size for retrieval
        ocr: Enable OCR for scanned content

    Returns:
        Dictionary with conversion results
    """
    pdf_path = Path(pdf_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    doc_name = pdf_path.stem
    assets_dir = output_dir / f"{doc_name}_assets"
    assets_dir.mkdir(exist_ok=True)

    print(f"Converting for Claude: {pdf_path.name}")

    # Configure pipeline for maximum extraction
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = ocr
    pipeline_options.do_table_structure = True
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    print("Processing document...")
    result = converter.convert(str(pdf_path))

    # Get full markdown
    markdown_content = result.document.export_to_markdown()

    # Save images
    image_count = 0
    image_map = {}
    if hasattr(result.document, "pictures"):
        for idx, picture in enumerate(result.document.pictures):
            if hasattr(picture, "image") and picture.image is not None:
                img_filename = f"image_{idx:03d}.png"
                img_path = assets_dir / img_filename
                picture.image.pil_image.save(str(img_path))
                image_map[f"image_{idx:03d}"] = str(img_path)
                image_count += 1

    print(f"Extracted {image_count} images")

    # Replace placeholders with image references
    image_idx = 0

    def replace_placeholder(match):
        nonlocal image_idx
        img_filename = f"image_{image_idx:03d}.png"
        img_path = assets_dir / img_filename
        if img_path.exists():
            relative_path = f"{doc_name}_assets/{img_filename}"
            replacement = f"![Image {image_idx}]({relative_path})"
            image_idx += 1
            return replacement
        return match.group(0)

    markdown_content = re.sub(r"<!-- image -->", replace_placeholder, markdown_content)

    # Create structured document with header
    header = _create_document_header(pdf_path)
    full_content = header + markdown_content

    # Save full markdown
    md_path = output_dir / f"{doc_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    # Create chunks for RAG
    chunks = _create_chunks(markdown_content, chunk_size)
    chunks_path = output_dir / f"{doc_name}_chunks.json"
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    # Create metadata file
    metadata = {
        "source_file": pdf_path.name,
        "converted_at": datetime.now().isoformat(),
        "markdown_path": str(md_path),
        "chunks_path": str(chunks_path),
        "num_chunks": len(chunks),
        "num_images": image_count,
        "images": image_map,
    }
    meta_path = output_dir / f"{doc_name}_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Created {len(chunks)} chunks")
    print(f"Saved: {md_path}")

    return {
        "markdown_path": str(md_path),
        "chunks_path": str(chunks_path),
        "metadata_path": str(meta_path),
        "num_chunks": len(chunks),
        "num_images": image_count,
    }


def _create_document_header(pdf_path: Path) -> str:
    """Create informative header for Claude."""
    header = f"""# {pdf_path.stem}

> **Source**: {pdf_path.name}
> **Converted**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
> **Type**: PDF Document

---

"""
    return header


def _create_chunks(content: str, target_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Split content into chunks optimized for retrieval.

    Preserves section boundaries where possible.
    """
    chunks = []
    sections = _split_by_sections(content)

    chunk_id = 0
    for section in sections:
        section_title = section.get("title", "")
        section_content = section.get("content", "")

        # If section is small enough, keep as one chunk
        if len(section_content) <= target_size * 1.5:
            chunks.append(
                {
                    "id": chunk_id,
                    "title": section_title,
                    "content": section_content,
                    "char_count": len(section_content),
                }
            )
            chunk_id += 1
        else:
            # Split large sections by paragraphs
            paragraphs = section_content.split("\n\n")
            current_chunk = ""

            for para in paragraphs:
                if len(current_chunk) + len(para) <= target_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(
                            {
                                "id": chunk_id,
                                "title": section_title,
                                "content": current_chunk.strip(),
                                "char_count": len(current_chunk),
                            }
                        )
                        chunk_id += 1
                    current_chunk = para + "\n\n"

            if current_chunk.strip():
                chunks.append(
                    {
                        "id": chunk_id,
                        "title": section_title,
                        "content": current_chunk.strip(),
                        "char_count": len(current_chunk),
                    }
                )
                chunk_id += 1

    return chunks


def _split_by_sections(content: str) -> List[Dict[str, str]]:
    """Split content by markdown headers."""
    sections = []
    pattern = r"^(#{1,3}\s+.+)$"
    parts = re.split(pattern, content, flags=re.MULTILINE)

    current_title = "Introduction"
    current_content = ""

    for part in parts:
        if re.match(r"^#{1,3}\s+", part):
            # Save previous section
            if current_content.strip():
                sections.append({"title": current_title, "content": current_content.strip()})
            current_title = part.strip("# \n")
            current_content = ""
        else:
            current_content += part

    # Don't forget last section
    if current_content.strip():
        sections.append({"title": current_title, "content": current_content.strip()})

    return sections


def build_knowledge_base(
    pdf_folder: str,
    output_folder: str,
    chunk_size: int = 1000,
    ocr: bool = True,
) -> Dict[str, Any]:
    """
    Build a complete knowledge base from multiple PDFs.

    Creates:
    - Individual markdown files
    - Chunk files for each document
    - Master index file
    - Combined metadata

    Args:
        pdf_folder: Directory containing PDFs
        output_folder: Output directory
        chunk_size: Chunk size for RAG
        ocr: Enable OCR

    Returns:
        Dictionary with build results
    """
    pdf_folder = Path(pdf_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    pdf_files = list(pdf_folder.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDFs found in {pdf_folder}")
        return {}

    print(f"Building knowledge base from {len(pdf_files)} documents...")

    all_results = []
    for pdf_file in pdf_files:
        try:
            result = convert_for_claude(
                str(pdf_file), str(output_folder), chunk_size=chunk_size, ocr=ocr
            )
            result["source"] = pdf_file.name
            all_results.append(result)
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")

    # Create master index
    index = _create_knowledge_index(output_folder, all_results)

    return {"documents": len(all_results), "index_path": index, "results": all_results}


def _create_knowledge_index(output_folder: Path, results: List[Dict]) -> str:
    """Create master index for the knowledge base."""
    index_content = """# Knowledge Base Index

This knowledge base contains converted documents for Claude agents.

## Documents

| Document | Chunks | Images |
|----------|--------|--------|
"""
    for r in results:
        source = r.get("source", "Unknown")
        chunks = r.get("num_chunks", 0)
        images = r.get("num_images", 0)
        index_content += f"| {source} | {chunks} | {images} |\n"

    index_content += """

## Usage with Claude

```python
# Load a document
with open("document_name.md", "r") as f:
    content = f.read()

# Or load chunks for RAG
import json
with open("document_name_chunks.json", "r") as f:
    chunks = json.load(f)
```

## File Structure

Each document creates:
- `document_name.md` - Full markdown content
- `document_name_chunks.json` - Chunked content for retrieval
- `document_name_metadata.json` - Document metadata
- `document_name_assets/` - Extracted images
"""

    index_path = output_folder / "INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    return str(index_path)
