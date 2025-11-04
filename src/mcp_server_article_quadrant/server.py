"""
Article Quadrant Analyzer MCP Server

An MCP server that extracts content from articles, performs insightful analysis,
and generates visual 2x2 quadrant representations using SVG graphics.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import fastmcp
from fastmcp import FastMCP, Context

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server_article_quadrant.tools.extract_content import extract_article_content
from mcp_server_article_quadrant.tools.analyze_insights import analyze_article_insights

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create the MCP server
app = FastMCP("article-quadrant-analyzer")


@app.tool()
async def extract_article_content(
    source: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract clean article content from URLs, local files, or direct text input with automatic preprocessing and metadata extraction.

    Args:
        source: Content source specification with type (url, file_path, direct_text) and content
        options: Extraction options including metadata extraction, HTML cleaning, timeouts

    Returns:
        Extracted content with title, text, metadata, and processing information
    """
    logger.info(f"Extracting content from source type: {source.get('type')}")
    return await extract_article_content(source, options)


@app.tool()
async def analyze_article_insights(
    content: Dict[str, Any],
    analysis_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract key insights, topics, and classifications from article content using natural language processing.

    Args:
        content: Article content with title, text, and metadata
        analysis_options: Analysis configuration including topic extraction, sentiment analysis, language settings

    Returns:
        Structured insights with topics, key points, entities, and sentiment analysis
    """
    logger.info("Analyzing article insights")
    return await analyze_article_insights(content, analysis_options)


@app.tool()
async def generate_quadrant_analysis(
    insights: Dict[str, Any],
    quadrant_config: Dict[str, Any],
    visualization_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive 2x2 quadrant analysis with professional SVG visualization based on article insights.

    Args:
        insights: Analysis results from analyze_article_insights
        quadrant_config: Quadrant configuration with axes and labels
        visualization_options: Visual styling options including colors, fonts, layout

    Returns:
        Complete quadrant analysis with SVG visualization and metadata
    """
    logger.info("Generating quadrant analysis")

    # This will be implemented in the tools/generate_quadrant.py module
    # For now, return a placeholder response
    return {
        "success": False,
        "error": {
            "code": "NOT_IMPLEMENTED",
            "message": "Tool implementation in progress"
        },
        "processing_time": 0.0
    }


@app.tool()
async def create_custom_quadrant(
    title: str,
    x_axis: Dict[str, Any],
    y_axis: Dict[str, Any],
    insights: list,
    styling: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create custom quadrant analysis with user-defined parameters and manual insight placement.

    Args:
        title: Analysis title
        x_axis: X-axis configuration with label and dimension settings
        y_axis: Y-axis configuration with label and dimension settings
        insights: List of insights with content and positioning information
        styling: Optional visual styling configuration

    Returns:
        Custom quadrant analysis with SVG visualization and positioning data
    """
    logger.info(f"Creating custom quadrant: {title}")

    # This will be implemented in the tools/create_custom_quadrant.py module
    # For now, return a placeholder response
    return {
        "success": False,
        "error": {
            "code": "NOT_IMPLEMENTED",
            "message": "Tool implementation in progress"
        },
        "processing_time": 0.0
    }


def main() -> None:
    """Main entry point for the MCP server."""
    logger.info("Starting Article Quadrant Analyzer MCP Server")

    # Get configuration from environment variables
    cache_dir = os.getenv("ANALYSIS_CACHE_DIR", "~/.cache/article-analyzer")
    max_content_length = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logger.info(f"Configuration: cache_dir={cache_dir}, max_content_length={max_content_length}, log_level={log_level}")

    # Run the server
    app.run()


if __name__ == "__main__":
    main()