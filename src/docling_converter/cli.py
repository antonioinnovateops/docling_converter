"""
Command-line interface for Docling Converter.
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .converter import convert_pdf_to_markdown, batch_convert
from .obsidian import convert_for_obsidian, batch_import_to_vault
from .knowledge import convert_for_claude, build_knowledge_base


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="docling-converter",
        description="Convert PDFs to Markdown for Claude & Obsidian",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  docling-converter convert document.pdf -o output/
  docling-converter convert --batch pdfs/ -o output/
  docling-converter obsidian document.pdf /path/to/vault
  docling-converter claude document.pdf -o knowledge/
  docling-converter claude --batch pdfs/ -o knowledge/
        """,
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert PDF to Markdown with images"
    )
    convert_parser.add_argument("input", help="PDF file or directory (with --batch)")
    convert_parser.add_argument(
        "-o", "--output", help="Output directory", default="."
    )
    convert_parser.add_argument(
        "--batch", action="store_true", help="Process all PDFs in directory"
    )
    convert_parser.add_argument(
        "--no-ocr", action="store_true", help="Disable OCR"
    )
    convert_parser.add_argument(
        "--image-scale",
        type=float,
        default=2.0,
        help="Image scale factor (default: 2.0)",
    )
    # PHASE 1-2: Mermaid diagram support
    convert_parser.add_argument(
        "--enable-diagram-classification",
        action="store_true",
        default=True,
        help="Enable diagram type detection (Phase 1, default: enabled)",
    )
    convert_parser.add_argument(
        "--no-diagram-classification",
        action="store_true",
        help="Disable diagram classification",
    )
    convert_parser.add_argument(
        "--enable-mermaid",
        action="store_true",
        help="Convert detected diagrams to mermaid format (Phase 2)",
    )
    convert_parser.add_argument(
        "--mermaid-format",
        choices=["mermaid", "svg", "png"],
        default="mermaid",
        help="Mermaid output format (default: mermaid)",
    )

    # Obsidian command
    obsidian_parser = subparsers.add_parser(
        "obsidian", help="Convert PDF for Obsidian vault"
    )
    obsidian_parser.add_argument("input", help="PDF file or directory (with --batch)")
    obsidian_parser.add_argument("vault", help="Obsidian vault path")
    obsidian_parser.add_argument(
        "--batch", action="store_true", help="Process all PDFs in directory"
    )
    obsidian_parser.add_argument(
        "--no-frontmatter", action="store_true", help="Skip YAML frontmatter"
    )
    obsidian_parser.add_argument(
        "--tags", nargs="+", default=["imported", "pdf"], help="Tags to add"
    )
    obsidian_parser.add_argument(
        "--no-ocr", action="store_true", help="Disable OCR"
    )
    # PHASE 3: Obsidian mermaid support
    obsidian_parser.add_argument(
        "--with-mermaid",
        action="store_true",
        help="Create diagram notes in vault with mermaid (Phase 3)",
    )
    obsidian_parser.add_argument(
        "--diagram-links",
        action="store_true",
        help="Create wiki-style links to diagram notes",
    )

    # Claude knowledge base command
    claude_parser = subparsers.add_parser(
        "claude", help="Convert PDF for Claude knowledge base"
    )
    claude_parser.add_argument("input", help="PDF file or directory (with --batch)")
    claude_parser.add_argument(
        "-o", "--output", help="Output directory", default="."
    )
    claude_parser.add_argument(
        "--batch", action="store_true", help="Process all PDFs in directory"
    )
    claude_parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size for RAG (default: 1000)",
    )
    claude_parser.add_argument(
        "--no-ocr", action="store_true", help="Disable OCR"
    )
    # PHASE 2-3: Mermaid support for Claude KB
    claude_parser.add_argument(
        "--with-mermaid",
        action="store_true",
        help="Include mermaid diagrams in knowledge base chunks (Phase 2)",
    )
    claude_parser.add_argument(
        "--extract-diagrams",
        action="store_true",
        help="Create separate diagram chunks for better retrieval (Phase 3)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "convert":
            _handle_convert(args)
        elif args.command == "obsidian":
            _handle_obsidian(args)
        elif args.command == "claude":
            _handle_claude(args)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def _handle_convert(args):
    """Handle convert command."""
    ocr = not args.no_ocr
    # PHASE 1-2: Mermaid support
    enable_diagram_classification = not args.no_diagram_classification
    enable_mermaid = args.enable_mermaid if hasattr(args, 'enable_mermaid') else False

    if args.batch:
        results = batch_convert(
            args.input,
            args.output,
            ocr=ocr,
            image_scale=args.image_scale,
            enable_diagram_classification=enable_diagram_classification,
            enable_mermaid=enable_mermaid,
        )
        print(f"\nConverted {len(results)} documents")
    else:
        result = convert_pdf_to_markdown(
            args.input,
            args.output,
            ocr=ocr,
            image_scale=args.image_scale,
            enable_diagram_classification=enable_diagram_classification,
            enable_mermaid=enable_mermaid,
        )
        print(f"\nOutput: {result}")


def _handle_obsidian(args):
    """Handle obsidian command."""
    ocr = not args.no_ocr
    add_frontmatter = not args.no_frontmatter
    # PHASE 3: Mermaid support for Obsidian
    with_mermaid = args.with_mermaid if hasattr(args, 'with_mermaid') else False
    diagram_links = args.diagram_links if hasattr(args, 'diagram_links') else False

    if args.batch:
        results = batch_import_to_vault(
            args.input,
            args.vault,
            tags=args.tags,
            ocr=ocr,
            enable_mermaid=with_mermaid,
        )
        print(f"\nImported {len(results)} documents to vault")
    else:
        result = convert_for_obsidian(
            args.input,
            args.vault,
            add_frontmatter=add_frontmatter,
            tags=args.tags,
            ocr=ocr,
            enable_mermaid=with_mermaid,
            diagram_links=diagram_links,
        )
        print(f"\nOutput: {result}")


def _handle_claude(args):
    """Handle claude command."""
    ocr = not args.no_ocr
    # PHASE 2-3: Mermaid support for Claude KB
    with_mermaid = args.with_mermaid if hasattr(args, 'with_mermaid') else False
    extract_diagrams = args.extract_diagrams if hasattr(args, 'extract_diagrams') else False

    if args.batch:
        results = build_knowledge_base(
            args.input,
            args.output,
            chunk_size=args.chunk_size,
            ocr=ocr,
            enable_mermaid=with_mermaid,
            extract_diagram_chunks=extract_diagrams,
        )
        print(f"\nBuilt knowledge base with {results.get('documents', 0)} documents")
        print(f"Index: {results.get('index_path', '')}")
    else:
        result = convert_for_claude(
            args.input,
            args.output,
            chunk_size=args.chunk_size,
            ocr=ocr,
            enable_mermaid=with_mermaid,
            extract_diagram_chunks=extract_diagrams,
        )
        print(f"\nOutput: {result['markdown_path']}")
        print(f"Chunks: {result['num_chunks']}")
        print(f"Images: {result['num_images']}")


if __name__ == "__main__":
    main()
