"""
Phase 2-3: Mermaid diagram conversion module.
Converts diagram images to mermaid syntax using Claude API or rule-based methods.
"""

import base64
import json
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess


def _read_image_as_base64(image_path: str) -> str:
    """Read an image file and encode as base64 for Claude API."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _get_diagram_type_description(diagram_type: str) -> str:
    """Get description of diagram type for Claude API prompt."""
    descriptions = {
        "FLOW_CHART": "a flowchart showing process steps and decisions",
        "ELECTRICAL_DIAGRAM": "an electrical circuit diagram with components and connections",
        "CAD_DRAWING": "a CAD (computer-aided design) technical drawing",
        "BAR_CHART": "a bar chart showing data values",
        "LINE_CHART": "a line chart showing trends over time",
        "PIE_CHART": "a pie chart showing proportions",
        "SCATTER_CHART": "a scatter plot showing data point distribution",
        "STACKED_BAR_CHART": "a stacked bar chart showing multiple data series",
        "HEATMAP": "a heatmap showing value intensity across dimensions",
        "GEOGRAPHIC_MAP": "a geographic/map diagram showing locations or regions",
        "SEQUENCE_DIAGRAM": "a sequence diagram showing interactions between components",
        "CLASS_DIAGRAM": "a UML class diagram showing class relationships",
        "STATE_DIAGRAM": "a state machine diagram showing state transitions",
    }
    return descriptions.get(diagram_type, "a diagram")


def convert_image_to_mermaid_via_claude(
    image_path: str,
    diagram_type: str,
    claude_api_key: Optional[str] = None,
    confidence: float = 0.7,
) -> Optional[str]:
    """
    Convert a diagram image to mermaid syntax using Claude API (PHASE 2).

    Args:
        image_path: Path to the diagram image
        diagram_type: Classification type of the diagram
        claude_api_key: Claude API key (optional, uses env var if not provided)
        confidence: Confidence threshold (currently unused, for future use)

    Returns:
        Mermaid diagram syntax as string, or None if conversion fails
    """
    try:
        import anthropic
    except ImportError:
        print("  (anthropic library not installed, install with: pip install anthropic)")
        return None

    # Get API key
    api_key = claude_api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  (ANTHROPIC_API_KEY not set, skipping mermaid conversion)")
        return None

    try:
        # Read and encode image
        image_data = _read_image_as_base64(image_path)

        # Create Claude client
        client = anthropic.Anthropic(api_key=api_key)

        # Get diagram type description for better prompting
        diagram_desc = _get_diagram_type_description(diagram_type)

        # Create prompt for Claude
        prompt = f"""Analyze this image which shows {diagram_desc}.

Convert this diagram to mermaid syntax. Important rules:
1. Only output valid mermaid code (no explanations)
2. Use appropriate mermaid diagram type based on content:
   - Flowcharts: use 'graph TD' or 'flowchart'
   - Sequences: use 'sequenceDiagram'
   - Classes: use 'classDiagram'
   - States: use 'stateDiagram-v2'
   - Gantt: use 'gantt'
3. Keep labels concise but descriptive
4. Preserve all important connections and labels from the original
5. Use proper mermaid syntax without any markdown code blocks

If the diagram is too complex or unclear to convert, return a minimal mermaid placeholder with the diagram name.

Return ONLY the mermaid code, nothing else."""

        # Call Claude API with vision capability
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        # Extract mermaid code from response
        mermaid_code = message.content[0].text.strip()

        # Validate mermaid syntax (basic check)
        if _validate_mermaid_syntax(mermaid_code):
            return mermaid_code
        else:
            print(f"  (Generated mermaid syntax validation failed)")
            return None

    except Exception as e:
        print(f"  (Claude API conversion error: {e})")
        return None


def _validate_mermaid_syntax(mermaid_code: str) -> bool:
    """Validate basic mermaid syntax (PHASE 3)."""
    if not mermaid_code:
        return False

    # Check for required mermaid diagram keywords
    valid_starts = [
        "graph",
        "flowchart",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "gantt",
        "pie",
        "erDiagram",
        "architecture",
    ]

    for start_keyword in valid_starts:
        if mermaid_code.strip().startswith(start_keyword):
            return True

    return False


def render_mermaid_to_svg(
    mermaid_code: str,
    output_path: str,
    theme: str = "default",
) -> Optional[str]:
    """
    Render mermaid code to SVG using mermaid-cli (PHASE 3).

    Args:
        mermaid_code: Mermaid diagram code
        output_path: Path to save SVG file
        theme: Mermaid theme (default, dark, forest, neutral)

    Returns:
        Path to generated SVG file, or None if rendering fails
    """
    try:
        # Check if mermaid-cli is installed
        subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"  (mermaid-cli not installed, install with: npm install -g @mermaid-js/mermaid-cli)")
        return None

    try:
        # Write mermaid code to temporary file
        mmd_path = output_path.replace(".svg", ".mmd")
        with open(mmd_path, "w") as f:
            f.write(mermaid_code)

        # Render to SVG
        cmd = [
            "mmdc",
            "-i",
            mmd_path,
            "-o",
            output_path,
            "--theme",
            theme,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return output_path
        else:
            print(f"  (mermaid rendering failed: {result.stderr})")
            return None

    except subprocess.TimeoutExpired:
        print(f"  (mermaid rendering timeout)")
        return None
    except Exception as e:
        print(f"  (mermaid rendering error: {e})")
        return None


def rule_based_diagram_converter(
    diagram_type: str,
    diagram_data: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Rule-based converter for specific diagram types (PHASE 3).

    This is a fallback for when Claude API is unavailable or for simple diagram types.

    Args:
        diagram_type: Classification type of the diagram
        diagram_data: Optional structured data extracted from diagram

    Returns:
        Basic mermaid syntax, or None if cannot convert
    """

    # Simple rule-based conversions for common diagram types
    if diagram_type == "FLOW_CHART":
        # Placeholder flowchart
        return """graph TD
    A["Process Start"] --> B["Action"]
    B --> C["Decision"]
    C -->|Yes| D["Success"]
    C -->|No| E["Try Again"]
    D --> F["End"]
    E --> B"""

    elif diagram_type == "BAR_CHART":
        # Placeholder bar chart as simple list
        return """---
config:
    xyChart:
        width: 900
        height: 600
    themeVariables:
        xyChart:
            plotColorPalette: "#2f54eb"
---
xychart-beta
    title "Data Distribution"
    x-axis [Item 1, Item 2, Item 3, Item 4]
    y-axis "Values" 0 --> 100
    line [20, 40, 60, 80]"""

    elif diagram_type == "SEQUENCE_DIAGRAM":
        return """sequenceDiagram
    participant A as Component A
    participant B as Component B
    A->>B: Request
    B->>A: Response
    Note over A,B: Interaction Complete"""

    elif diagram_type == "STATE_DIAGRAM":
        return """stateDiagram-v2
    [*] --> State1
    State1 --> State2: Transition
    State2 --> State3: Transition
    State3 --> [*]"""

    else:
        # Generic diagram placeholder
        return f"""graph TD
    A["Diagram: {diagram_type}"]
    A --> B["(Please manually create mermaid version)"]"""


def create_mermaid_markdown_section(
    image_filename: str,
    diagram_type: str,
    mermaid_code: Optional[str],
    confidence: float = 0.7,
) -> str:
    """
    Create a markdown section containing mermaid diagram with fallback image (PHASE 3).

    Args:
        image_filename: Original image filename
        diagram_type: Diagram type classification
        mermaid_code: Mermaid syntax code (optional)
        confidence: Confidence score of the classification

    Returns:
        Formatted markdown section
    """

    section = f"""## Diagram: {diagram_type}\n"""
    section += f"*Classification confidence: {confidence:.1%}*\n\n"

    if mermaid_code:
        section += f"""```mermaid\n{mermaid_code}\n```\n\n"""

    # Add fallback image
    relative_path = f"diagram_assets/{image_filename}"
    section += f"""![{diagram_type} Diagram]({relative_path})\n\n"""

    return section
