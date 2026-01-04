"""
Core PDF to Markdown converter module with mermaid diagram support.
"""

import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption


def convert_pdf_to_markdown(
    pdf_path: str,
    output_dir: Optional[str] = None,
    extract_images: bool = True,
    ocr: bool = True,
    image_scale: float = 2.0,
    enable_diagram_classification: bool = True,
    enable_mermaid: bool = False,
    mermaid_format: str = "mermaid",  # mermaid, svg, png
) -> str:
    """
    Convert a PDF to Markdown with images extracted to relative paths.

    NEW: Supports diagram classification and mermaid diagram extraction.

    Args:
        pdf_path: Path to the input PDF file
        output_dir: Output directory (defaults to same as PDF)
        extract_images: Whether to extract and save images
        ocr: Enable OCR for scanned content
        image_scale: Scale factor for extracted images
        enable_diagram_classification: Enable diagram type detection (Phase 1)
        enable_mermaid: Convert detected diagrams to mermaid format (Phase 2)
        mermaid_format: Output format for mermaid (mermaid, svg, png)

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
    pipeline_options.do_ocr = ocr
    pipeline_options.do_table_structure = True
    pipeline_options.images_scale = image_scale
    pipeline_options.generate_picture_images = True

    # PHASE 1: Enable diagram classification (NEW)
    if enable_diagram_classification:
        pipeline_options.do_picture_classification = True
        print("✓ Diagram classification enabled")

    # Create converter with PDF options
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Convert document
    print("Processing document (this may take a while for large PDFs)...")
    result = converter.convert(str(pdf_path))

    # Export to markdown
    markdown_content = result.document.export_to_markdown()

    # PHASE 1: Save images with classification metadata (NEW)
    image_count = 0
    diagram_count = 0
    classification_data: Dict[str, Any] = {
        "source": str(pdf_path),
        "images": [],
        "diagrams": [],
    }

    if extract_images and hasattr(result.document, "pictures"):
        for idx, picture in enumerate(result.document.pictures):
            if hasattr(picture, "image") and picture.image is not None:
                img_filename = f"image_{idx:03d}.png"
                img_path = assets_dir / img_filename
                picture.image.pil_image.save(str(img_path))
                image_count += 1

                # PHASE 1: Extract classification metadata (NEW)
                image_metadata = {
                    "index": idx,
                    "filename": img_filename,
                    "size": {
                        "width": picture.image.pil_image.width,
                        "height": picture.image.pil_image.height,
                    },
                }

                # Add classification if available
                if enable_diagram_classification and hasattr(picture, "meta") and hasattr(picture.meta, "classification"):
                    classifications = picture.meta.classification.predictions
                    if classifications:
                        top_classification = classifications[0]
                        image_metadata["classification"] = {
                            "type": str(top_classification.class_name),
                            "confidence": float(top_classification.confidence),
                            "is_diagram": _is_diagram_type(str(top_classification.class_name)),
                        }
                        classification_data["images"].append(image_metadata)

                        # Track diagrams separately
                        if image_metadata["classification"]["is_diagram"]:
                            diagram_count += 1
                            classification_data["diagrams"].append(image_metadata)
                            print(f"  Diagram detected: {image_metadata['classification']['type']} (confidence: {image_metadata['classification']['confidence']:.2f})")
                    else:
                        classification_data["images"].append(image_metadata)
                else:
                    classification_data["images"].append(image_metadata)

    print(f"Extracted {image_count} images ({diagram_count} diagrams)")

    # PHASE 1: Save classification metadata (NEW)
    if enable_diagram_classification and (image_count > 0):
        metadata_path = output_dir / f"{doc_name}_classification.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(classification_data, f, indent=2)
        print(f"Classification metadata saved: {metadata_path}")

    # Replace <!-- image --> placeholders with actual image references
    image_placeholder_pattern = r"<!-- image -->"
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
        image_placeholder_pattern, replace_image_placeholder, markdown_content
    )

    # Save markdown file
    md_path = output_dir / f"{doc_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Markdown saved: {md_path}")

    return str(md_path)


def _is_diagram_type(classification_type: str) -> bool:
    """Check if a classification type represents a diagram (PHASE 1)"""
    diagram_types = {
        "FLOW_CHART",
        "ELECTRICAL_DIAGRAM",
        "CAD_DRAWING",
        "BAR_CHART",
        "LINE_CHART",
        "PIE_CHART",
        "SCATTER_CHART",
        "STACKED_BAR_CHART",
        "HEATMAP",
        "MOLECULAR_STRUCTURE",
        "MARKUSH_STRUCTURE",
        "STRATIGRAPHIC_CHART",
        "GEOGRAPHIC_MAP",
        "REMOTE_SENSING",
    }
    return classification_type in diagram_types


def _convert_diagram_to_mermaid(
    image_path: str,
    diagram_type: str,
    enable_mermaid: bool = False,
    use_claude_api: bool = True,
    claude_api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Convert a diagram image to mermaid format (PHASE 2-3).

    Args:
        image_path: Path to the diagram image
        diagram_type: Classification type of the diagram
        enable_mermaid: Whether to attempt conversion
        use_claude_api: Use Claude API for conversion (Phase 2)
        claude_api_key: Claude API key (optional, uses env var if not provided)

    Returns:
        Mermaid diagram syntax as string, or None if conversion fails
    """
    if not enable_mermaid:
        return None

    # Phase 2: Claude API integration
    if use_claude_api:
        try:
            from mermaid_converter import convert_image_to_mermaid_via_claude
            return convert_image_to_mermaid_via_claude(image_path, diagram_type, claude_api_key)
        except ImportError:
            print("  (Claude API mermaid_converter not available, skipping Phase 2 conversion)")
            return None
        except Exception as e:
            print(f"  Error converting to mermaid: {e}")
            return None

    return None


def batch_convert(
    input_dir: str,
    output_dir: Optional[str] = None,
    ocr: bool = True,
    image_scale: float = 2.0,
    enable_diagram_classification: bool = True,
    enable_mermaid: bool = False,
) -> List[str]:
    """
    Convert all PDFs in a directory.

    Args:
        input_dir: Directory containing PDFs
        output_dir: Output directory for all conversions
        ocr: Enable OCR for scanned content
        image_scale: Scale factor for extracted images
        enable_diagram_classification: Enable diagram detection (Phase 1)
        enable_mermaid: Convert diagrams to mermaid (Phase 2)

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
            md_path = convert_pdf_to_markdown(
                str(pdf_file),
                output_dir,
                ocr=ocr,
                image_scale=image_scale,
                enable_diagram_classification=enable_diagram_classification,
                enable_mermaid=enable_mermaid,
            )
            results.append(md_path)
        except Exception as e:
            print(f"Error converting {pdf_file.name}: {e}")

    return results
