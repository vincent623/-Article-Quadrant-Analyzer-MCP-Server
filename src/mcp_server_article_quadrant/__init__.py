"""
Article Quadrant Analyzer MCP Server

An MCP server that extracts content from articles, performs insightful analysis,
and generates visual 2x2 quadrant representations using SVG graphics.
"""

__version__ = "1.0.0"
__author__ = "Article Quadrant Analyzer Team"

from .server import main

__all__ = ["main", "__version__"]