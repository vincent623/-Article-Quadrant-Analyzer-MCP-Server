"""MCP tool for generating 2x2 quadrant analysis with SVG visualization."""

import logging
import time
from typing import Dict, Any, Optional

from mcp_server_article_quadrant.utils.quadrant_generator import QuadrantGenerator
from mcp_server_article_quadrant.utils.error_handling import handle_error, ErrorContext


logger = logging.getLogger(__name__)

# Global quadrant generator instance
_quadrant_generator: Optional[QuadrantGenerator] = None


def get_quadrant_generator() -> QuadrantGenerator:
    """Get or create global quadrant generator instance."""
    global _quadrant_generator
    if _quadrant_generator is None:
        _quadrant_generator = QuadrantGenerator()
    return _quadrant_generator


async def generate_quadrant_analysis(
    insights: Dict[str, Any],
    quadrant_config: Dict[str, Any],
    visualization_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive 2x2 quadrant analysis with professional SVG visualization based on article insights.

    This tool transforms text analysis insights into visual quadrant diagrams, helping to:
    - Classify insights based on custom dimensions (importance, urgency, impact, etc.)
    - Create strategic visualizations for decision-making
    - Generate professional SVG diagrams for presentations
    - Identify patterns and relationships in content insights

    Args:
        insights: Analysis results from analyze_article_insights containing:
            - main_topics: List of extracted topics with relevance scores
            - key_points: List of key insights with importance and sentiment
            - entities: List of named entities with frequency and confidence
            - overall_sentiment: Sentiment analysis with polarity and label
            - statistics: Text statistics and readability metrics
        quadrant_config: Quadrant configuration with axes and labels:
            - x_axis: X-axis configuration (label, min_label, max_label, dimension)
            - y_axis: Y-axis configuration (label, min_label, max_label, dimension)
            - quadrant_labels: Optional labels for Q1, Q2, Q3, Q4
            - title: Optional analysis title
        visualization_options: Visual styling options:
            - width: SVG width in pixels (default: 500)
            - height: SVG height in pixels (default: 500)
            - color_scheme: Color scheme (professional, vibrant, monochrome) (default: professional)
            - show_legend: Show legend (default: true)
            - show_grid: Show grid lines (default: true)
            - show_labels: Show axis and quadrant labels (default: true)

    Returns:
        Dictionary containing:
        - success: Whether generation was successful
        - quadrant_analysis: Complete quadrant analysis with:
            - svg_content: SVG visualization string
            - quadrants: Array of quadrant data with insights
            - summary: Analysis summary with key findings
            - config_used: Configuration used for generation
        - metadata: Generation metadata and processing info
        - processing_time: Time taken for generation in seconds
        - error: Error details (if generation failed)

    Example usage:
        # Generate impact vs. effort quadrant
        result = await generate_quadrant_analysis(
            insights,  # From analyze_article_insights
            {
                "x_axis": {
                    "label": "Impact",
                    "min_label": "Low",
                    "max_label": "High",
                    "dimension": "impact"
                },
                "y_axis": {
                    "label": "Effort",
                    "min_label": "Low",
                    "max_label": "High",
                    "dimension": "complexity"
                },
                "quadrant_labels": [
                    "High Impact, High Effort",
                    "High Impact, Low Effort",
                    "Low Impact, Low Effort",
                    "Low Impact, High Effort"
                ],
                "title": "Strategic Initiative Analysis"
            },
            {
                "width": 600,
                "height": 600,
                "color_scheme": "professional"
            }
        )
    """
    start_time = time.time()
    options = visualization_options or {}

    try:
        with ErrorContext("generate_quadrant_analysis", context={
            "insights_count": len(insights.get("key_points", [])) if insights else 0
        }):
            logger.info("Generating quadrant analysis from insights")

            # Validate insights input
            if not isinstance(insights, dict):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Insights must be a dictionary",
                        "details": {"received_type": type(insights).__name__}
                    },
                    "processing_time": time.time() - start_time
                }

            # Validate that insights contain some data
            key_points = insights.get("key_points", [])
            main_topics = insights.get("main_topics", [])
            entities = insights.get("entities", [])

            if not key_points and not main_topics and not entities:
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Insights must contain at least one of: key_points, main_topics, entities",
                        "details": {
                            "key_points_count": len(key_points),
                            "main_topics_count": len(main_topics),
                            "entities_count": len(entities)
                        }
                    },
                    "processing_time": time.time() - start_time
                }

            # Validate quadrant configuration
            if not isinstance(quadrant_config, dict):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Quadrant configuration must be a dictionary",
                        "details": {"received_type": type(quadrant_config).__name__}
                    },
                    "processing_time": time.time() - start_time
                }

            # Validate required axis configuration
            x_axis = quadrant_config.get("x_axis")
            y_axis = quadrant_config.get("y_axis")

            if not x_axis or not isinstance(x_axis, dict):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Quadrant configuration must include 'x_axis'",
                        "details": {"x_axis": x_axis}
                    },
                    "processing_time": time.time() - start_time
                }

            if not y_axis or not isinstance(y_axis, dict):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Quadrant configuration must include 'y_axis'",
                        "details": {"y_axis": y_axis}
                    },
                    "processing_time": time.time() - start_time
                }

            # Validate axis labels
            if not x_axis.get("label"):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "X-axis must have a 'label'",
                        "details": {"x_axis": x_axis}
                    },
                    "processing_time": time.time() - start_time
                }

            if not y_axis.get("label"):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Y-axis must have a 'label'",
                        "details": {"y_axis": y_axis}
                    },
                    "processing_time": time.time() - start_time
                }

            # Set default visualization options
            default_options = {
                "width": 500,
                "height": 500,
                "color_scheme": "professional",
                "show_legend": True,
                "show_grid": True,
                "show_labels": True
            }
            visualization_options = {**default_options, **options}

            # Validate visualization options
            width = visualization_options.get("width", 500)
            height = visualization_options.get("height", 500)

            if not isinstance(width, int) or width < 300 or width > 1000:
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Width must be an integer between 300 and 1000",
                        "details": {"width": width, "valid_range": [300, 1000]}
                    },
                    "processing_time": time.time() - start_time
                }

            if not isinstance(height, int) or height < 300 or height > 1000:
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Height must be an integer between 300 and 1000",
                        "details": {"height": height, "valid_range": [300, 1000]}
                    },
                    "processing_time": time.time() - start_time
                }

            # Get quadrant generator and create analysis
            generator = get_quadrant_generator()
            result = await generator.generate_quadrant_analysis(
                insights, quadrant_config, visualization_options
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            if result.get("success"):
                # Standardize successful response
                quadrant_analysis = result.get("quadrant_analysis", {})

                # Validate that SVG content was generated
                svg_content = quadrant_analysis.get("svg_content")
                if not svg_content or not isinstance(svg_content, str):
                    return {
                        "success": False,
                        "error": {
                            "type": "GenerationError",
                            "message": "Failed to generate SVG visualization",
                            "details": {"svg_content_type": type(svg_content).__name__}
                        },
                        "processing_time": processing_time
                    }

                # Enhanced metadata
                enhanced_metadata = {
                    **result.get("metadata", {}),
                    "generation_timestamp": time.time(),
                    "insights_summary": {
                        "key_points": len(key_points),
                        "main_topics": len(main_topics),
                        "entities": len(entities)
                    },
                    "visualization_options": visualization_options,
                    "server_version": "1.0.0"
                }

                standardized_response = {
                    "success": True,
                    "quadrant_analysis": quadrant_analysis,
                    "metadata": enhanced_metadata,
                    "processing_time": processing_time
                }

                logger.info(f"Successfully generated quadrant analysis in {processing_time:.2f}s")
                return standardized_response

            else:
                # Standardize error response
                error_data = result.get("error", {})
                if isinstance(error_data, dict):
                    error_data.update({
                        "processing_time": processing_time,
                        "insights_processed": len(key_points) + len(main_topics) + len(entities)
                    })

                return {
                    "success": False,
                    "error": error_data,
                    "processing_time": processing_time
                }

    except Exception as e:
        logger.error(f"Unexpected error in generate_quadrant_analysis: {e}")
        processing_time = time.time() - start_time

        return handle_error(
            e,
            context={
                "insights": insights,
                "quadrant_config": quadrant_config,
                "visualization_options": visualization_options,
                "processing_time": processing_time
            },
            logger=logger
        )


# Tool metadata for FastMCP
TOOL_METADATA = {
    "name": "generate_quadrant_analysis",
    "description": """
Generate comprehensive 2x2 quadrant analysis with professional SVG visualization based on article insights.

This tool transforms text analysis insights into visual quadrant diagrams for strategic analysis:
- Classifies insights based on custom dimensions (importance, urgency, impact, etc.)
- Creates professional SVG visualizations suitable for presentations
- Identifies patterns and relationships in content insights
- Provides strategic recommendations based on quadrant distribution

The visualization includes:
- Color-coded quadrants with customizable labels
- Positioned insights with importance-based sizing
- Axis labels and grid lines for clarity
- Legend and summary statistics
- Professional styling with multiple color schemes
""",
    "annotations": {
        "readOnlyHint": True,  # Analysis generation is read-only
        "destructiveHint": False,  # Non-destructive visualization
        "idempotentHint": True,  # Same insights produce consistent quadrants
        "openWorldHint": False  # Deterministic visualization generation
    },
    "input_schema": {
        "type": "object",
        "properties": {
            "insights": {
                "type": "object",
                "description": "Analysis results from analyze_article_insights",
                "properties": {
                    "main_topics": {
                        "type": "array",
                        "description": "List of extracted topics",
                        "items": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "relevance": {"type": "number"},
                                "keywords": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "key_points": {
                        "type": "array",
                        "description": "List of key insights",
                        "items": {
                            "type": "object",
                            "properties": {
                                "point": {"type": "string"},
                                "importance": {"type": "number"},
                                "sentiment": {"type": "string"}
                            }
                        }
                    },
                    "entities": {
                        "type": "array",
                        "description": "List of named entities",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "type": {"type": "string"},
                                "frequency": {"type": "integer"}
                            }
                        }
                    },
                    "overall_sentiment": {
                        "type": "object",
                        "description": "Overall sentiment analysis",
                        "properties": {
                            "polarity": {"type": "number"},
                            "label": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    }
                }
            },
            "quadrant_config": {
                "type": "object",
                "description": "Quadrant configuration parameters",
                "properties": {
                    "x_axis": {
                        "type": "object",
                        "description": "X-axis configuration",
                        "properties": {
                            "label": {
                                "type": "string",
                                "description": "X-axis label",
                                "examples": ["Impact", "Importance", "Cost", "Time"]
                            },
                            "min_label": {
                                "type": "string",
                                "description": "Label for minimum end of X-axis",
                                "examples": ["Low", "Slow", "Cheap"]
                            },
                            "max_label": {
                                "type": "string",
                                "description": "Label for maximum end of X-axis",
                                "examples": ["High", "Fast", "Expensive"]
                            },
                            "dimension": {
                                "type": "string",
                                "enum": ["importance", "sentiment", "novelty", "practicality", "custom"],
                                "description": "Predefined dimension type",
                                "default": "importance"
                            }
                        },
                        "required": ["label"]
                    },
                    "y_axis": {
                        "type": "object",
                        "description": "Y-axis configuration",
                        "properties": {
                            "label": {
                                "type": "string",
                                "description": "Y-axis label",
                                "examples": ["Effort", "Urgency", "Risk", "Complexity"]
                            },
                            "min_label": {
                                "type": "string",
                                "description": "Label for minimum end of Y-axis",
                                "examples": ["Low", "Easy", "Safe"]
                            },
                            "max_label": {
                                "type": "string",
                                "description": "Label for maximum end of Y-axis",
                                "examples": ["High", "Difficult", "Risky"]
                            },
                            "dimension": {
                                "type": "string",
                                "enum": ["urgency", "impact", "feasibility", "complexity", "custom"],
                                "description": "Predefined dimension type",
                                "default": "complexity"
                            }
                        },
                        "required": ["label"]
                    },
                    "quadrant_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels for Q1, Q2, Q3, Q4",
                        "minItems": 4,
                        "maxItems": 4,
                        "examples": [
                            ["Quick Wins", "Major Projects", "Fill-ins", "Thankless Tasks"],
                            ["High Impact, High Effort", "High Impact, Low Effort", "Low Impact, Low Effort", "Low Impact, High Effort"]
                        ]
                    },
                    "title": {
                        "type": "string",
                        "description": "Analysis title",
                        "examples": ["Strategic Initiative Analysis", "Risk Assessment Matrix", "Feature Prioritization"]
                    }
                },
                "required": ["x_axis", "y_axis"]
            },
            "visualization_options": {
                "type": "object",
                "description": "Visual styling options",
                "properties": {
                    "width": {
                        "type": "integer",
                        "default": 500,
                        "minimum": 300,
                        "maximum": 1000,
                        "description": "SVG width in pixels"
                    },
                    "height": {
                        "type": "integer",
                        "default": 500,
                        "minimum": 300,
                        "maximum": 1000,
                        "description": "SVG height in pixels"
                    },
                    "color_scheme": {
                        "type": "string",
                        "default": "professional",
                        "enum": ["professional", "vibrant", "monochrome", "custom"],
                        "description": "Color scheme for visualization"
                    },
                    "show_legend": {
                        "type": "boolean",
                        "default": True,
                        "description": "Show legend"
                    },
                    "show_grid": {
                        "type": "boolean",
                        "default": True,
                        "description": "Show grid lines"
                    },
                    "show_labels": {
                        "type": "boolean",
                        "default": True,
                        "description": "Show axis and quadrant labels"
                    }
                }
            }
        },
        "required": ["insights", "quadrant_config"]
    },
    "examples": [
        {
            "description": "Generate strategic impact vs. effort quadrant",
            "input": {
                "insights": {
                    "key_points": [
                        {
                            "point": "Implement AI-powered customer service chatbot",
                            "importance": 0.9,
                            "sentiment": "positive"
                        },
                        {
                            "point": "Upgrade legacy CRM system",
                            "importance": 0.7,
                            "sentiment": "neutral"
                        },
                        {
                            "point": "Optimize website loading speed",
                            "importance": 0.6,
                            "sentiment": "positive"
                        }
                    ],
                    "main_topics": [
                        {
                            "topic": "Digital Transformation",
                            "relevance": 0.8,
                            "keywords": ["AI", "automation", "digital"]
                        }
                    ]
                },
                "quadrant_config": {
                    "x_axis": {
                        "label": "Impact",
                        "min_label": "Low",
                        "max_label": "High",
                        "dimension": "importance"
                    },
                    "y_axis": {
                        "label": "Effort",
                        "min_label": "Low",
                        "max_label": "High",
                        "dimension": "complexity"
                    },
                    "quadrant_labels": [
                        "Major Projects",
                        "Quick Wins",
                        "Fill-ins",
                        "Thankless Tasks"
                    ],
                    "title": "Strategic Initiative Analysis"
                },
                "visualization_options": {
                    "width": 600,
                    "height": 600,
                    "color_scheme": "professional"
                }
            }
        }
    ]
}