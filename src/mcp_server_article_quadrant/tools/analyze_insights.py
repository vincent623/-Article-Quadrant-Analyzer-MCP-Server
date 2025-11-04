"""MCP tool for analyzing insights from article content."""

import logging
import time
from typing import Dict, Any, Optional

from mcp_server_article_quadrant.utils.text_analyzer import TextAnalyzer
from mcp_server_article_quadrant.utils.error_handling import handle_error, ErrorContext


logger = logging.getLogger(__name__)

# Global text analyzer instance
_text_analyzer: Optional[TextAnalyzer] = None


def get_text_analyzer() -> TextAnalyzer:
    """Get or create global text analyzer instance."""
    global _text_analyzer
    if _text_analyzer is None:
        _text_analyzer = TextAnalyzer()
    return _text_analyzer


async def analyze_article_insights(
    content: Dict[str, Any],
    analysis_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract key insights, topics, and classifications from article content using natural language processing.

    This tool performs comprehensive text analysis including:
    - Topic modeling and keyword extraction
    - Sentiment analysis and tone detection
    - Named entity recognition (people, organizations, locations)
    - Key point extraction and importance scoring
    - Text statistics and readability analysis
    - Language detection and processing

    Args:
        content: Article content dictionary containing:
            - title: Article title (optional)
            - text: Main article text (required)
            - metadata: Additional metadata about the content (optional)
        analysis_options: Analysis configuration options:
            - extract_topics: Extract main topics and themes (default: true)
            - sentiment_analysis: Analyze sentiment and tone (default: true)
            - key_entities: Extract named entities (default: true)
            - language: Content language (auto, en, zh, etc.) (default: "auto")
            - max_insights: Maximum number of insights to extract (default: 20)
            - include_statistics: Include text statistics (default: true)

    Returns:
        Dictionary containing:
        - success: Whether analysis was successful
        - insights: Analysis results with topics, key points, entities, and sentiment
        - metadata: Analysis metadata including processing time and confidence
        - summary: Brief summary of analysis results
        - processing_time: Time taken for analysis in seconds
        - error: Error details (if analysis failed)

    Example usage:
        # Analyze extracted article content
        result = await analyze_article_insights({
            "title": "The Future of AI in Healthcare",
            "text": "Artificial intelligence is revolutionizing healthcare...",
            "metadata": {"source": "tech_journal", "author": "Dr. Smith"}
        }, {
            "extract_topics": True,
            "sentiment_analysis": True,
            "max_insights": 15
        })
    """
    start_time = time.time()
    options = analysis_options or {}

    try:
        with ErrorContext("analyze_article_insights", context={"content_length": len(content.get("text", ""))}):
            logger.info("Starting article insights analysis")

            # Validate content input
            if not isinstance(content, dict):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Content must be a dictionary",
                        "details": {"received_type": type(content).__name__}
                    },
                    "processing_time": time.time() - start_time
                }

            # Validate required text field
            text = content.get("text")
            if not text or not isinstance(text, str):
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Content must include a 'text' field with string value",
                        "details": {"text_type": type(text).__name__ if text is not None else "missing"}
                    },
                    "processing_time": time.time() - start_time
                }

            # Check minimum text length
            text_length = len(text.strip())
            if text_length < 50:
                return {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": f"Text too short for meaningful analysis: {text_length} characters (minimum: 50)",
                        "details": {"actual_length": text_length, "minimum_length": 50}
                    },
                    "processing_time": time.time() - start_time
                }

            # Set default analysis options
            default_options = {
                "extract_topics": True,
                "sentiment_analysis": True,
                "key_entities": True,
                "language": "auto",
                "max_insights": 20,
                "include_statistics": True
            }
            analysis_options = {**default_options, **options}

            # Get text analyzer and perform analysis
            analyzer = get_text_analyzer()
            result = await analyzer.analyze_text(content, analysis_options)

            # Calculate processing time
            processing_time = time.time() - start_time

            if result.get("success"):
                # Standardize successful response
                insights = result.get("insights", {})
                metadata = result.get("metadata", {})

                # Validate insights structure
                standardized_insights = {
                    "main_topics": insights.get("main_topics", []),
                    "key_points": insights.get("key_points", []),
                    "entities": insights.get("entities", []),
                    "overall_sentiment": insights.get("overall_sentiment"),
                    "statistics": insights.get("statistics")
                }

                # Add additional analysis metadata
                enhanced_metadata = {
                    **metadata,
                    "content_info": {
                        "title": content.get("title"),
                        "text_length": text_length,
                        "word_count": len(text.split()),
                        "has_metadata": bool(content.get("metadata"))
                    },
                    "analysis_timestamp": time.time(),
                    "server_version": "1.0.0"
                }

                # Generate detailed summary if not provided
                summary = result.get("summary")
                if not summary:
                    summary = _generate_analysis_summary(standardized_insights, content.get("title"))

                standardized_response = {
                    "success": True,
                    "insights": standardized_insights,
                    "metadata": enhanced_metadata,
                    "summary": summary,
                    "processing_time": processing_time
                }

                logger.info(f"Successfully analyzed article insights in {processing_time:.2f}s")
                return standardized_response

            else:
                # Standardize error response
                error_data = result.get("error", {})
                if isinstance(error_data, dict):
                    error_data.update({
                        "processing_time": processing_time,
                        "text_length": text_length
                    })

                return {
                    "success": False,
                    "error": error_data,
                    "processing_time": processing_time
                }

    except Exception as e:
        logger.error(f"Unexpected error in analyze_article_insights: {e}")
        processing_time = time.time() - start_time

        return handle_error(
            e,
            context={
                "content_length": len(content.get("text", "")) if content else 0,
                "options": options,
                "processing_time": processing_time
            },
            logger=logger
        )


def _generate_analysis_summary(insights: Dict[str, Any], title: Optional[str] = None) -> str:
    """Generate a comprehensive summary of the analysis results."""
    try:
        summary_parts = []

        # Add title if available
        if title:
            summary_parts.append(f"Analysis of '{title}'")

        # Main topics
        topics = insights.get("main_topics", [])[:3]
        if topics:
            topic_names = [t.get("topic", "Unknown Topic") for t in topics]
            summary_parts.append(f"Primary topics: {', '.join(topic_names)}")

        # Key insights
        key_points = insights.get("key_points", [])
        if key_points:
            summary_parts.append(f"Extracted {len(key_points)} key insights")

            # Add most important insight
            if key_points:
                top_point = key_points[0].get("point", "")
                if top_point:
                    truncated_point = top_point[:100] + "..." if len(top_point) > 100 else top_point
                    summary_parts.append(f"Key insight: {truncated_point}")

        # Entities
        entities = insights.get("entities", [])
        if entities:
            entity_types = {}
            for entity in entities:
                entity_type = entity.get("type", "UNKNOWN")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            if entity_types:
                type_summary = ", ".join([f"{count} {entity_type.lower()}" for entity_type, count in entity_types.items()])
                summary_parts.append(f"Identified {type_summary}")

        # Sentiment
        sentiment = insights.get("overall_sentiment")
        if sentiment:
            sentiment_label = sentiment.get("label", "neutral")
            sentiment_score = sentiment.get("polarity", 0)
            confidence = sentiment.get("confidence", 0)

            sentiment_desc = sentiment_label.replace("_", " ")
            if confidence > 0.7:
                summary_parts.append(f"Overall sentiment: {sentiment_desc} (confidence: {confidence:.1%})")
            else:
                summary_parts.append(f"Overall sentiment: {sentiment_desc}")

        # Statistics
        stats = insights.get("statistics")
        if stats:
            word_count = stats.get("word_count", 0)
            complexity = stats.get("complexity_level", "unknown")
            summary_parts.append(f"Text complexity: {complexity.replace('_', ' ')} ({word_count:,} words)")

        return ". ".join(summary_parts) + "."

    except Exception as e:
        logger.error(f"Failed to generate analysis summary: {e}")
        return "Text analysis completed successfully."


# Tool metadata for FastMCP
TOOL_METADATA = {
    "name": "analyze_article_insights",
    "description": """
Extract key insights, topics, and classifications from article content using natural language processing.

This tool performs comprehensive text analysis including:
- Topic modeling and keyword extraction with relevance scoring
- Sentiment analysis with polarity and confidence metrics
- Named entity recognition (people, organizations, locations, dates)
- Key point extraction with importance scoring
- Text statistics and readability analysis
- Multi-language support (English, Chinese, and more)

The analysis transforms raw text into structured insights suitable for strategic analysis,
content categorization, and quadrant classification.
""",
    "annotations": {
        "readOnlyHint": True,  # Content analysis is read-only
        "destructiveHint": False,  # Non-destructive analysis
        "idempotentHint": True,  # Same content produces consistent insights
        "openWorldHint": False  # Analysis depends only on provided content
    },
    "input_schema": {
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "description": "Article content for analysis",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Article title",
                        "examples": ["The Future of AI in Healthcare", "Climate Change Impacts on Agriculture"]
                    },
                    "text": {
                        "type": "string",
                        "description": "Main article text content",
                        "minLength": 50,
                        "examples": [
                            "Artificial intelligence is transforming healthcare by enabling more accurate diagnoses...",
                            "Climate change is significantly impacting agricultural productivity worldwide..."
                        ]
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional content metadata",
                        "properties": {
                            "author": {"type": "string"},
                            "source_url": {"type": "string"},
                            "publication_date": {"type": "string"},
                            "language": {"type": "string"}
                        }
                    }
                },
                "required": ["text"]
            },
            "analysis_options": {
                "type": "object",
                "description": "Analysis configuration options",
                "properties": {
                    "extract_topics": {
                        "type": "boolean",
                        "default": True,
                        "description": "Extract main topics and themes"
                    },
                    "sentiment_analysis": {
                        "type": "boolean",
                        "default": True,
                        "description": "Analyze sentiment and tone"
                    },
                    "key_entities": {
                        "type": "boolean",
                        "default": True,
                        "description": "Extract named entities"
                    },
                    "language": {
                        "type": "string",
                        "default": "auto",
                        "enum": ["auto", "en", "zh", "es", "fr", "de", "ja"],
                        "description": "Content language (auto, en, zh, etc.)"
                    },
                    "max_insights": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 5,
                        "maximum": 100,
                        "description": "Maximum number of insights to extract"
                    },
                    "include_statistics": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include text statistics and readability metrics"
                    }
                }
            }
        },
        "required": ["content"]
    },
    "examples": [
        {
            "description": "Analyze a technology article",
            "input": {
                "content": {
                    "title": "The Rise of Machine Learning in Business",
                    "text": """
Machine learning is revolutionizing business operations across industries. Companies are leveraging
predictive analytics to forecast market trends, optimize supply chains, and personalize customer
experiences. Natural language processing enables automated customer service, while computer vision
powers quality control and security systems. The integration of ML technologies has led to
significant improvements in efficiency and decision-making processes.

However, challenges remain in data privacy, algorithmic bias, and the need for skilled personnel.
Organizations must balance innovation with ethical considerations and regulatory compliance.
                    """.strip(),
                    "metadata": {
                        "author": "Tech Analyst",
                        "source_url": "https://example.com/ml-business"
                    }
                },
                "analysis_options": {
                    "extract_topics": True,
                    "sentiment_analysis": True,
                    "max_insights": 15
                }
            }
        },
        {
            "description": "Analyze content in Chinese",
            "input": {
                "content": {
                    "title": "人工智能在医疗领域的应用",
                    "text": """
人工智能正在医疗领域发挥越来越重要的作用。通过深度学习算法，医生可以更准确地诊断疾病，
识别医学影像中的异常模式。AI系统还能分析大量患者数据，预测疾病风险，制定个性化治疗方案。

在药物研发方面，人工智能大大缩短了新药开发周期，降低了研发成本。智能医疗助手可以
24小时不间断地为患者提供健康咨询和用药指导。远程医疗结合AI技术，让偏远地区的患者
也能获得优质的医疗服务。

然而，AI医疗应用也面临数据隐私保护、算法公平性、监管审批等挑战。医疗机构需要
在技术创新和患者安全之间找到平衡点。
                    """.strip()
                },
                "analysis_options": {
                    "language": "zh",
                    "extract_topics": True,
                    "key_entities": True
                }
            }
        },
        {
            "description": "Analyze with custom options",
            "input": {
                "content": {
                    "text": """
Climate change represents one of the most pressing challenges of our time. Rising global temperatures
are leading to more extreme weather events, sea-level rise, and disruptions to ecosystems worldwide.
The scientific consensus is clear: human activities, particularly the burning of fossil fuels,
are the primary driver of these changes.

Renewable energy technologies offer hope for reducing greenhouse gas emissions. Solar and wind power
are becoming increasingly cost-effective, while energy storage solutions are addressing intermittency
challenges. Governments and businesses are investing heavily in clean energy infrastructure.

Individual actions also matter. Reducing energy consumption, adopting sustainable transportation,
and supporting environmentally responsible companies can collectively make a significant impact.
                    """.strip()
                },
                "analysis_options": {
                    "extract_topics": True,
                    "sentiment_analysis": True,
                    "key_entities": True,
                    "include_statistics": True,
                    "max_insights": 25
                }
            }
        }
    ]
}