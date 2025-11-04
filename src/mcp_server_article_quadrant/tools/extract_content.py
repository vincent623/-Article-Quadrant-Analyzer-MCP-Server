"""MCP tool for extracting content from various sources."""

import logging
import time
from typing import Dict, Any, Optional

from mcp_server_article_quadrant.models.content import ContentSource, ContentExtractionOptions, ContentExtractionResult
from mcp_server_article_quadrant.utils.content_extractor import ContentExtractor
from mcp_server_article_quadrant.utils.error_handling import handle_error, ErrorContext


logger = logging.getLogger(__name__)

# Global content extractor instance
_content_extractor: Optional[ContentExtractor] = None


def get_content_extractor() -> ContentExtractor:
    """Get or create global content extractor instance."""
    global _content_extractor
    if _content_extractor is None:
        _content_extractor = ContentExtractor()
    return _content_extractor


async def extract_article_content(
    source: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract clean article content from URLs, local files, or direct text input with automatic preprocessing and metadata extraction.

    This tool supports multiple content sources:
    - URLs: Web pages, news articles, blog posts, WeChat public accounts
    - Files: PDF, TXT, MD, DOCX documents
    - Images: PNG, JPG, WEBP screenshots (with OCR)
    - Direct text: Manual text input

    Args:
        source: Content source specification containing:
            - type: Source type ("url", "file_path", "direct_text")
            - content: URL, file path, or direct text content
            - encoding: Text encoding for file processing (default: "utf-8")
        options: Extraction options including:
            - extract_metadata: Extract title, author, publication date (default: true)
            - clean_html: Remove HTML tags and clean content (default: true)
            - min_length: Minimum content length in characters (default: 100)
            - timeout: Timeout in seconds for URL processing (default: 30)
            - max_content_length: Maximum content length to process (default: 50000)
            - max_file_size_mb: Maximum file size in MB (default: 50)
            - language: Content language for OCR/analysis (default: "auto")

    Returns:
        Dictionary containing:
        - success: Whether extraction was successful
        - content: Extracted content with title, text, and metadata (if successful)
        - processing_time: Time taken for extraction in seconds
        - warnings: Processing warnings (if any)
        - error: Error details (if extraction failed)

    Example usage:
        # Extract from URL
        result = await extract_article_content({
            "type": "url",
            "content": "https://example.com/article"
        })

        # Extract from file
        result = await extract_article_content({
            "type": "file_path",
            "content": "/path/to/document.pdf",
            "encoding": "utf-8"
        })

        # Extract from image (OCR)
        result = await extract_article_content({
            "type": "file_path",
            "content": "/path/to/screenshot.png"
        })

        # Direct text input
        result = await extract_article_content({
            "type": "direct_text",
            "content": "This is the article content to analyze..."
        })
    """
    start_time = time.time()
    options = options or {}

    try:
        with ErrorContext("extract_article_content", context={"source_type": source.get("type")}):
            logger.info(f"Extracting content from source type: {source.get('type')}")

            # Validate source
            if not isinstance(source, dict):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Source must be a dictionary",
                        "details": {"received_type": type(source).__name__}
                    },
                    "processing_time": time.time() - start_time
                }

            # Validate required fields
            source_type = source.get("type")
            content = source.get("content")

            if not source_type:
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Source must include 'type' field",
                        "details": {"missing_field": "type"}
                    },
                    "processing_time": time.time() - start_time
                }

            if not content:
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Source must include 'content' field",
                        "details": {"missing_field": "content"}
                    },
                    "processing_time": time.time() - start_time
                }

            # Validate source type
            valid_types = ["url", "file_path", "direct_text"]
            if source_type not in valid_types:
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": f"Invalid source type '{source_type}'. Valid types: {valid_types}",
                        "details": {"valid_types": valid_types, "received_type": source_type}
                    },
                    "processing_time": time.time() - start_time
                }

            # Set default options
            default_options = {
                "extract_metadata": True,
                "clean_html": True,
                "min_length": 100,
                "timeout": 30,
                "max_content_length": 50000,
                "max_file_size_mb": 50,
                "encoding": "utf-8",
                "language": "auto"
            }
            extraction_options = {**default_options, **options}

            # Add source encoding to options if specified
            if "encoding" in source:
                extraction_options["encoding"] = source["encoding"]

            # Get content extractor and extract content
            extractor = get_content_extractor()
            result = await extractor.extract_content(source, extraction_options)

            # Calculate processing time
            processing_time = time.time() - start_time

            if result.get("success"):
                # Standardize successful response
                content_data = result.get("content", {})

                # Ensure content has required fields
                if not isinstance(content_data, dict):
                    content_data = {}

                standardized_response = {
                    "success": True,
                    "content": {
                        "title": content_data.get("title"),
                        "text": content_data.get("text", ""),
                        "metadata": content_data.get("metadata", {}),
                        "sections": content_data.get("sections"),
                        "links": content_data.get("links")
                    },
                    "processing_time": processing_time,
                    "warnings": result.get("warnings", [])
                }

                # Add metadata about extraction
                if standardized_response["content"]["metadata"]:
                    standardized_response["content"]["metadata"]["extraction_timestamp"] = time.time()
                    standardized_response["content"]["metadata"]["source_type"] = source_type
                    standardized_response["content"]["metadata"]["processing_options"] = extraction_options

                logger.info(f"Successfully extracted content from {source_type} source in {processing_time:.2f}s")
                return standardized_response

            else:
                # Standardize error response
                error_data = result.get("error", {})
                if isinstance(error_data, dict):
                    error_data.update({
                        "processing_time": processing_time,
                        "source_type": source_type
                    })

                return {
                    "success": False,
                    "error": error_data,
                    "processing_time": processing_time
                }

    except Exception as e:
        logger.error(f"Unexpected error in extract_article_content: {e}")
        processing_time = time.time() - start_time

        return handle_error(
            e,
            context={
                "source": source,
                "options": options,
                "processing_time": processing_time
            },
            logger=logger
        )


# Tool metadata for FastMCP
TOOL_METADATA = {
    "name": "extract_article_content",
    "description": """
Extract clean article content from URLs, local files, or direct text input with automatic preprocessing and metadata extraction.

Supports multiple content sources:
- URLs: Web pages, news articles, blog posts, WeChat public accounts
- Files: PDF, TXT, MD, DOCX documents
- Images: PNG, JPG, WEBP screenshots (with OCR)
- Direct text: Manual text input

Features:
- Automatic content cleaning and preprocessing
- Metadata extraction (title, author, publication date)
- OCR support for images and scanned documents
- Multi-language support (English, Chinese, etc.)
- Configurable processing limits and timeouts
""",
    "annotations": {
        "readOnlyHint": False,  # May modify content through cleaning
        "destructiveHint": False,  # Content extraction is non-destructive
        "idempotentHint": True,  # Same input produces same output
        "openWorldHint": True  # External URLs introduce open-world assumptions
    },
    "input_schema": {
        "type": "object",
        "properties": {
            "source": {
                "type": "object",
                "description": "Content source specification",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["url", "file_path", "direct_text"],
                        "description": "Type of content source",
                        "examples": ["url", "file_path", "direct_text"]
                    },
                    "content": {
                        "type": "string",
                        "description": "URL, file path, or direct text content",
                        "examples": [
                            "https://example.com/article",
                            "/path/to/document.pdf",
                            "This is the article content to analyze..."
                        ]
                    },
                    "encoding": {
                        "type": "string",
                        "default": "utf-8",
                        "description": "Text encoding for file processing",
                        "examples": ["utf-8", "gbk", "latin-1"]
                    }
                },
                "required": ["type", "content"]
            },
            "options": {
                "type": "object",
                "description": "Extraction options",
                "properties": {
                    "extract_metadata": {
                        "type": "boolean",
                        "default": True,
                        "description": "Extract title, author, publication date"
                    },
                    "clean_html": {
                        "type": "boolean",
                        "default": True,
                        "description": "Remove HTML tags and clean content"
                    },
                    "min_length": {
                        "type": "integer",
                        "default": 100,
                        "minimum": 10,
                        "maximum": 1000,
                        "description": "Minimum content length in characters"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "minimum": 5,
                        "maximum": 300,
                        "description": "Timeout in seconds for URL processing"
                    },
                    "max_content_length": {
                        "type": "integer",
                        "default": 50000,
                        "minimum": 1000,
                        "maximum": 200000,
                        "description": "Maximum content length to process"
                    },
                    "max_file_size_mb": {
                        "type": "integer",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200,
                        "description": "Maximum file size in MB"
                    },
                    "language": {
                        "type": "string",
                        "default": "auto",
                        "enum": ["auto", "en", "zh", "es", "fr", "de", "ja"],
                        "description": "Content language for OCR/analysis"
                    }
                }
            }
        },
        "required": ["source"]
    },
    "examples": [
        {
            "description": "Extract content from a news article URL",
            "input": {
                "source": {
                    "type": "url",
                    "content": "https://www.bbc.com/news/technology-123456"
                },
                "options": {
                    "timeout": 30,
                    "max_content_length": 10000
                }
            }
        },
        {
            "description": "Extract text from a PDF document",
            "input": {
                "source": {
                    "type": "file_path",
                    "content": "/path/to/research.pdf"
                },
                "options": {
                    "max_file_size_mb": 20,
                    "extract_metadata": True
                }
            }
        },
        {
            "description": "Extract text from a screenshot using OCR",
            "input": {
                "source": {
                    "type": "file_path",
                    "content": "/path/to/screenshot.png"
                },
                "options": {
                    "language": "auto"
                }
            }
        },
        {
            "description": "Process direct text input",
            "input": {
                "source": {
                    "type": "direct_text",
                    "content": """
Artificial intelligence is transforming healthcare by enabling more accurate diagnoses,
personalized treatment plans, and predictive analytics. Machine learning algorithms can
analyze medical images, detect patterns in patient data, and assist in drug discovery.
These technologies have the potential to improve patient outcomes while reducing costs.
                    """.strip()
                },
                "options": {
                    "extract_metadata": True
                }
            }
        }
    ]
}