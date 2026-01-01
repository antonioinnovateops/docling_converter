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

    if args.batch:
        results = batch_convert(
            args.input, args.output, ocr=ocr, image_scale=args.image_scale
        )
        print(f"\nConverted {len(results)} documents")
    else:
        result = convert_pdf_to_markdown(
            args.input, args.output, ocr=ocr, image_scale=args.image_scale
        )
        print(f"\nOutput: {result}")


def _handle_obsidian(args):
    """Handle obsidian command."""
    ocr = not args.no_ocr
    add_frontmatter = not args.no_frontmatter

    if args.batch:
        results = batch_import_to_vault(
            args.input, args.vault, tags=args.tags, ocr=ocr
        )
        print(f"\nImported {len(results)} documents to vault")
    else:
        result = convert_for_obsidian(
            args.input,
            args.vault,
            add_frontmatter=add_frontmatter,
            tags=args.tags,
            ocr=ocr,
        )
        print(f"\nOutput: {result}")


def _handle_claude(args):
    """Handle claude command."""
    ocr = not args.no_ocr

    if args.batch:
        results = build_knowledge_base(
            args.input, args.output, chunk_size=args.chunk_size, ocr=ocr
        )
        print(f"\nBuilt knowledge base with {results.get('documents', 0)} documents")
        print(f"Index: {results.get('index_path', '')}")
    else:
        result = convert_for_claude(
            args.input, args.output, chunk_size=args.chunk_size, ocr=ocr
        )
        print(f"\nOutput: {result['markdown_path']}")
        print(f"Chunks: {result['num_chunks']}")
        print(f"Images: {result['num_images']}")


if __name__ == "__main__":
    main()
