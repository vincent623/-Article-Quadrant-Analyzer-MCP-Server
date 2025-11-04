# Article Quadrant Analyzer MCP Server Specification

## Server Overview

### Name
**article-quadrant-analyzer**

### Purpose
An MCP server that extracts content from articles, performs insightful analysis, and generates visual 2x2 quadrant representations using SVG graphics. The server transforms textual content into structured insights and presents them in an intuitive visual format.

### Target Integrations
- **Claude Desktop**: Primary integration for local article analysis
- **Content Analysis Workflows**: Support for researchers, analysts, and content strategists
- **Visual Documentation**: Generation of quadrant diagrams for reports and presentations

### Primary Use Cases
1. **Content Analysis**: Extract key insights from articles, blog posts, and research papers
2. **Strategic Evaluation**: Classify content using custom 2x2 quadrant frameworks
3. **Visual Communication**: Generate professional SVG quadrant diagrams for presentations
4. **Comparative Analysis**: Compare multiple articles or perspectives using consistent frameworks

## Transport Protocol

### Selected Protocol: **STDIO**

### Rationale
- **Claude Desktop Integration**: Native support and zero-configuration setup
- **Performance**: Optimal for local processing with minimal overhead
- **Security**: Process isolation and no network exposure for core functionality
- **Simplicity**: Easy deployment and debugging capabilities

### Configuration
```json
{
    "mcpServers": {
        "article-quadrant-analyzer": {
            "command": "python",
            "args": ["-m", "article_quadrant_analyzer.server"],
            "env": {
                "ANALYSIS_CACHE_DIR": "~/.cache/article-analyzer",
                "MAX_CONTENT_LENGTH": "50000",
                "LOG_LEVEL": "INFO"
            }
        }
    }
}
```

## Tool Specifications

### 1. extract_article_content

**Purpose**: Extract clean article content from URLs, local files, or direct text input with automatic preprocessing and metadata extraction.

**Value Proposition**: Provides unified content extraction from multiple sources while removing noise and preserving essential information.

**Annotations**:
- `readOnlyHint`: false - May modify content through cleaning
- `destructiveHint`: false - Content extraction is non-destructive
- `idempotentHint`: true - Same input produces same output
- `openWorldHint`: true - External URLs introduce open-world assumptions

**Input Schema**:
```json
{
    "type": "object",
    "properties": {
        "source": {
            "type": "object",
            "description": "Content source specification",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["url", "file_path", "direct_text"],
                    "description": "Type of content source"
                },
                "content": {
                    "type": "string",
                    "description": "URL, file path, or direct text content"
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "Text encoding for file processing"
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
                    "default": true,
                    "description": "Extract title, author, publication date"
                },
                "clean_html": {
                    "type": "boolean",
                    "default": true,
                    "description": "Remove HTML tags and clean content"
                },
                "min_length": {
                    "type": "integer",
                    "default": 100,
                    "description": "Minimum content length in characters"
                },
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "Timeout in seconds for URL processing"
                }
            }
        }
    },
    "required": ["source"]
}
```

**Output Format**: JSON

**Output Schema**:
```json
{
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether extraction was successful"
        },
        "content": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Article title"
                },
                "text": {
                    "type": "string",
                    "description": "Clean article content"
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "author": {"type": "string"},
                        "publication_date": {"type": "string"},
                        "source_url": {"type": "string"},
                        "word_count": {"type": "integer"},
                        "language": {"type": "string"}
                    }
                }
            }
        },
        "error": {
            "type": "object",
            "description": "Error details if extraction failed",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "details": {"type": "object"}
            }
        }
    }
}
```

**Error Handling**:
- **Network Errors**: Timeout, connection refused, rate limiting
- **File Errors**: Not found, permission denied, encoding issues
- **Content Errors**: Too short, access restricted, malformed content
- **Validation Errors**: Invalid URL, unsupported file type

### 2. analyze_article_insights

**Purpose**: Extract key insights, topics, and classifications from article content using natural language processing.

**Value Proposition**: Transforms raw text into structured, actionable insights suitable for strategic analysis and quadrant classification.

**Annotations**:
- `readOnlyHint`: true - Content analysis is read-only
- `destructiveHint`: false - Non-destructive analysis
- `idempotentHint`: true - Same content produces consistent insights
- `openWorldHint`: false - Analysis depends only on provided content

**Input Schema**:
```json
{
    "type": "object",
    "properties": {
        "content": {
            "type": "object",
            "description": "Article content for analysis",
            "properties": {
                "title": {"type": "string"},
                "text": {"type": "string"},
                "metadata": {"type": "object"}
            },
            "required": ["text"]
        },
        "analysis_options": {
            "type": "object",
            "description": "Analysis configuration options",
            "properties": {
                "extract_topics": {
                    "type": "boolean",
                    "default": true,
                    "description": "Extract main topics and themes"
                },
                "sentiment_analysis": {
                    "type": "boolean",
                    "default": true,
                    "description": "Analyze sentiment and tone"
                },
                "key_entities": {
                    "type": "boolean",
                    "default": true,
                    "description": "Extract named entities"
                },
                "language": {
                    "type": "string",
                    "default": "auto",
                    "description": "Content language (auto, zh, en)"
                },
                "max_insights": {
                    "type": "integer",
                    "default": 20,
                    "description": "Maximum number of insights to extract"
                }
            }
        }
    },
    "required": ["content"]
}
```

**Output Format**: JSON

**Error Handling**:
- **Content Errors**: Empty content, unsupported language, too short
- **Processing Errors**: NLP model failures, memory constraints
- **Timeout Errors**: Analysis taking too long for large content
- **Validation Errors**: Invalid parameters, malformed input

### 3. generate_quadrant_analysis

**Purpose**: Generate comprehensive 2x2 quadrant analysis with professional SVG visualization based on article insights.

**Value Proposition**: Creates visually compelling quadrant analyses that highlight strategic relationships and patterns in article content.

**Annotations**:
- `readOnlyHint`: true - Analysis generation is read-only
- `destructiveHint`: false - Non-destructive visualization
- `idempotentHint`: true - Same insights produce consistent quadrants
- `openWorldHint`: false - Deterministic visualization generation

**Input Schema**:
```json
{
    "type": "object",
    "properties": {
        "insights": {
            "type": "object",
            "description": "Analysis results from analyze_article_insights"
        },
        "quadrant_config": {
            "type": "object",
            "description": "Quadrant configuration parameters",
            "properties": {
                "x_axis": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "min_label": {"type": "string"},
                        "max_label": {"type": "string"},
                        "dimension": {
                            "type": "string",
                            "enum": ["importance", "sentiment", "novelty", "practicality", "custom"]
                        }
                    },
                    "required": ["label"]
                },
                "y_axis": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "min_label": {"type": "string"},
                        "max_label": {"type": "string"},
                        "dimension": {
                            "type": "string",
                            "enum": ["urgency", "impact", "feasibility", "complexity", "custom"]
                        }
                    },
                    "required": ["label"]
                },
                "quadrant_labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labels for Q1, Q2, Q3, Q4",
                    "minItems": 4,
                    "maxItems": 4
                }
            },
            "required": ["x_axis", "y_axis"]
        },
        "visualization_options": {
            "type": "object",
            "description": "Visual styling options",
            "properties": {
                "width": {"type": "integer", "default": 500, "minimum": 300, "maximum": 1000},
                "height": {"type": "integer", "default": 500, "minimum": 300, "maximum": 1000},
                "color_scheme": {
                    "type": "string",
                    "default": "professional",
                    "enum": ["professional", "vibrant", "monochrome", "custom"]
                },
                "show_legend": {"type": "boolean", "default": true},
                "show_grid": {"type": "boolean", "default": true},
                "title": {"type": "string"}
            }
        }
    },
    "required": ["insights", "quadrant_config"]
}
```

**Output Format**: JSON with embedded SVG

**Error Handling**:
- **Configuration Errors**: Invalid quadrant parameters, missing required fields
- **Visualization Errors**: SVG generation failures, layout issues
- **Data Errors**: Insufficient insights for quadrant placement
- **Rendering Errors**: Color scheme issues, font problems

### 4. create_custom_quadrant

**Purpose**: Create custom quadrant analysis with user-defined parameters and manual insight placement.

**Value Proposition**: Enables users to create tailored quadrant analyses with specific criteria and full control over insight placement.

**Annotations**:
- `readOnlyHint`: true - Creation is read-only
- `destructiveHint`: false - Non-destructive generation
- `idempotentHint`: true - Same input produces identical output
- `openWorldHint`: false - Deterministic custom quadrant creation

**Input Schema**:
```json
{
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Analysis title"
        },
        "x_axis": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "min_label": {"type": "string"},
                "max_label": {"type": "string"}
            },
            "required": ["label"]
        },
        "y_axis": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "min_label": {"type": "string"},
                "max_label": {"type": "string"}
            },
            "required": ["label"]
        },
        "insights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "x_position": {"type": "number", "minimum": -1, "maximum": 1},
                    "y_position": {"type": "number", "minimum": -1, "maximum": 1},
                    "quadrant": {
                        "type": "string",
                        "enum": ["Q1", "Q2", "Q3", "Q4"]
                    },
                    "weight": {"type": "number", "default": 1.0, "minimum": 0.1, "maximum": 5.0}
                },
                "required": ["content"]
            }
        },
        "styling": {
            "type": "object",
            "properties": {
                "color_scheme": {"type": "string"},
                "font_size": {"type": "integer", "minimum": 8, "maximum": 24},
                "show_labels": {"type": "boolean", "default": true},
                "background_color": {"type": "string"}
            }
        }
    },
    "required": ["title", "x_axis", "y_axis", "insights"]
}
```

**Output Format**: JSON with embedded SVG

**Error Handling**:
- **Validation Errors**: Invalid coordinates, missing required fields
- **Layout Errors**: Too many insights for display space
- **Styling Errors**: Invalid color formats, font issues
- **Generation Errors**: SVG creation failures

## Shared Infrastructure

### API Request Helpers
```python
class ContentExtractor:
    """Unified content extraction from multiple sources"""
    
    async def extract_from_url(self, url: str, options: dict) -> dict:
        """Extract content from web URLs"""
        
    async def extract_from_file(self, file_path: str, encoding: str) -> dict:
        """Extract content from local files"""
        
    def clean_direct_text(self, text: str) -> dict:
        """Process direct text input"""

class InsightAnalyzer:
    """Natural language processing for insight extraction"""
    
    async def extract_topics(self, text: str, max_topics: int) -> list:
        """Extract main topics using NLP"""
        
    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment and tone"""
        
    async def extract_entities(self, text: str) -> list:
        """Extract named entities"""

class QuadrantGenerator:
    """SVG quadrant visualization generation"""
    
    def create_svg_template(self, config: dict) -> str:
        """Generate base SVG structure"""
        
    def place_insights(self, insights: list, quadrants: dict) -> dict:
        """Position insights in appropriate quadrants"""
        
    def apply_styling(self, svg: str, style: dict) -> str:
        """Apply visual styling to SVG"""
```

### Error Handling Utilities
```python
class AnalysisError(Exception):
    """Base exception for analysis errors"""
    
class ContentExtractionError(AnalysisError):
    """Content extraction specific errors"""
    
class VisualizationError(AnalysisError):
    """Quadrant visualization errors"""

def handle_error(error: Exception, context: dict) -> dict:
    """Standardized error response formatting"""
    return {
        "success": False,
        "error": {
            "type": error.__class__.__name__,
            "message": str(error),
            "context": context,
            "suggested_action": get_error_guidance(error)
        }
    }
```

## Non-Functional Requirements

### Character Limit Strategies
**Default Context Limit**: 25,000 tokens
- **Content Extraction**: Truncate large articles to 50,000 characters
- **Insight Analysis**: Limit to top 20 insights by relevance
- **Quadrant Generation**: Maximum 15 insights per quadrant
- **Response Optimization**: Use concise JSON with essential metadata

### Rate Limiting and Timeout Handling
```python
class RateLimiter:
    """Rate limiting for external requests"""
    
    def __init__(self):
        self.url_requests = {}
        self.max_requests_per_minute = 30
        
    async def check_rate_limit(self, domain: str) -> bool:
        """Check if domain request limit exceeded"""

class TimeoutManager:
    """Operation timeout management"""
    
    CONTENT_EXTRACTION_TIMEOUT = 30  # seconds
    INSIGHT_ANALYSIS_TIMEOUT = 60   # seconds
    QUADRANT_GENERATION_TIMEOUT = 30  # seconds
```

## Deployment Configuration

### Transport Protocol Details
**Protocol**: STDIO
**Process Model**: Single process per Claude Desktop session
**Communication**: JSON-RPC 2.0 over stdin/stdout
**Process Lifecycle**: Session-based, starts with Claude Desktop

### Environment Variables
```bash
# Core Configuration
ANALYSIS_CACHE_DIR=~/.cache/article-analyzer
MAX_CONTENT_LENGTH=50000
LOG_LEVEL=INFO

# Processing Limits
DEFAULT_TIMEOUT=30
MAX_CONCURRENT_ANALYSES=3
INSIGHT_CACHE_TTL=3600

# External Services
ENABLE_WEB_SCRAPING=true
USER_AGENT=ArticleQuadrantAnalyzer/1.0
REQUEST_TIMEOUT=30
```

### Dependencies
```python
# Core dependencies
fastmcp>=0.1.0
asyncio-mqtt>=0.11.0
pydantic>=2.0.0

# Content extraction
newspaper3k>=0.2.8
beautifulsoup4>=4.12.0
readability-lxml>=0.8.1

# Text analysis
nltk>=3.8.0
spaCy>=3.6.0
transformers>=4.30.0

# Visualization
svgwrite>=1.4.3
pillow>=10.0.0

# Utilities
aiohttp>=3.8.0
python-dotenv>=1.0.0
```

## Evaluation Scenarios

### Scenario 1: Strategic Analysis of Tech Article
**Input**: URL of a technology trend analysis article
**Workflow**:
1. Extract article content from URL
2. Analyze insights for trends and implications
3. Generate quadrant with "Impact vs. Feasibility" axes
4. Create SVG visualization with professional styling

**Expected Output**: Professional quadrant diagram showing 15-20 key insights strategically positioned

### Scenario 2: Research Paper Comparison
**Input**: Two academic paper PDFs on similar topics
**Workflow**:
1. Extract content from both PDF files
2. Analyze and compare insights from both papers
3. Generate comparative quadrant analysis
4. Create visual comparison with consistent framework

**Expected Output**: Side-by-side quadrant analysis highlighting research consensus and divergence

### Scenario 3: Business Strategy Document
**Input**: Internal business strategy document (direct text)
**Workflow**:
1. Process direct text input
2. Extract strategic initiatives and market insights
3. Create custom quadrant with "Market Opportunity vs. Implementation Complexity"
4. Generate executive-ready visualization

**Expected Output**: Executive-level quadrant diagram suitable for board presentations

### Scenario 4: Content Marketing Analysis
**Input**: URLs of 5 competitor blog posts
**Workflow**:
1. Extract content from multiple URLs (batch processing)
2. Analyze content themes and engagement factors
3. Generate quadrant with "Content Value vs. Production Effort"
4. Create competitive positioning map

**Expected Output**: Competitive analysis quadrant showing content strategy gaps and opportunities

### Scenario 5: Product Feature Prioritization
**Input**: Customer feedback and feature requests
**Workflow**:
1. Extract insights from customer feedback data
2. Analyze feature importance and implementation complexity
3. Generate custom product roadmap quadrant
4. Create prioritization visualization

**Expected Output**: Product roadmap quadrant with clear feature prioritization guidance

### Scenario 6: Risk Assessment Matrix
**Input**: Project risk documentation
**Workflow**:
1. Extract risk factors and impact assessments
2. Analyze probability and impact metrics
3. Generate risk assessment quadrant
4. Create risk mitigation visualization

**Expected Output**: Risk matrix quadrant with clear risk categorization and mitigation priorities

### Scenario 7: Market Trend Analysis
**Input**: Industry report with trend data
**Workflow**:
1. Extract trend information from report
2. Analyze market impact and timeline factors
3. Generate trend adoption quadrant
4. Create strategic planning visualization

**Expected Output**: Market trend quadrant showing adoption timing and strategic importance

### Scenario 8: Content Quality Assessment
**Input**: Multiple articles for quality evaluation
**Workflow**:
1. Extract content from various sources
2. Analyze content quality metrics
3. Generate quality assessment quadrant
4. Create content strategy recommendations

**Expected Output**: Quality assessment quadrant with actionable content improvement insights

### Scenario 9: Investment Opportunity Analysis
**Input**: Investment research documents
**Workflow**:
1. Extract investment opportunities and risks
2. Analyze return potential and risk factors
3. Generate investment quadrant analysis
4. Create portfolio allocation visualization

**Expected Output**: Investment opportunity quadrant with risk-return profiling

### Scenario 10: Custom Framework Application
**Input**: User-defined analysis framework
**Workflow**:
1. Create custom quadrant configuration
2. Apply framework to specific content
3. Generate custom visualization
4. Export results in multiple formats

**Expected Output**: Fully customized quadrant analysis based on user-defined criteria

## Testing and Validation

### Unit Test Coverage
- Content extraction from all source types
- Insight analysis algorithms
- Quadrant generation logic
- SVG rendering accuracy
- Error handling scenarios

### Integration Testing
- End-to-end workflow testing
- Claude Desktop integration validation
- Performance benchmarking
- Memory usage optimization

### User Acceptance Testing
- Real-world article analysis
- Visualization quality assessment
- Error message clarity
- Overall user experience evaluation

## Conclusion

The Article Quadrant Analyzer MCP Server provides a comprehensive solution for transforming textual content into strategic visual insights. With robust content extraction, intelligent analysis, and professional visualization capabilities, it serves as an essential tool for researchers, analysts, and strategic thinkers.

The server's STDIO transport ensures seamless integration with Claude Desktop while maintaining high performance and security. The modular tool design allows for flexible workflows and extensibility for future enhancements.

**Key Success Factors**:
1. **Reliable Content Extraction**: Multi-source support with robust error handling
2. **Intelligent Analysis**: Meaningful insight extraction using advanced NLP
3. **Professional Visualization**: High-quality SVG quadrant generation
4. **Claude Desktop Integration**: Seamless user experience with zero configuration
5. **Extensibility**: Modular design supporting future enhancements

This specification provides the foundation for implementing a powerful, user-friendly article analysis tool that enhances strategic thinking and decision-making through visual quadrant analysis.
