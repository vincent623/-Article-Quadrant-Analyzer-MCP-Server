# Tool Design - Article Quadrant Analyzer MCP Server

## Overview
This document defines the tool architecture and design for the Article Quadrant Analyzer MCP Server. The tools are designed to provide a complete workflow from content extraction to visual quadrant analysis.

## Tool Architecture

### Core Tools
1. **extract_article_content** - Extract content from various sources
2. **analyze_article_insights** - Extract key insights and classify content
3. **generate_quadrant_analysis** - Create 2x2 quadrant analysis with SVG visualization
4. **create_custom_quadrant** - Generate custom quadrant analysis with user-defined parameters

### Supporting Tools
1. **validate_content_source** - Validate and preprocess content sources
2. **preview_analysis** - Provide analysis preview before full processing
3. **export_results** - Export analysis results in various formats

## Detailed Tool Specifications

### 1. extract_article_content

**Purpose**: Extract clean article content from URLs, files, or direct text input.

**Value Proposition**: Provides unified content extraction from multiple sources with automatic cleaning and preprocessing.

**Input Schema**:
```json
{
  "source": {
    "type": "object",
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
}
```

**Output Schema**:
```json
{
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
    "description": "Error details if extraction failed"
  }
}
```

**Error Handling**:
- Network timeouts for URL extraction
- File not found or permission errors
- Invalid URL formats
- Content access restrictions
- Encoding issues

### 2. analyze_article_insights

**Purpose**: Extract key insights, topics, and classifications from article content.

**Value Proposition**: Transforms raw content into structured insights suitable for quadrant analysis.

**Input Schema**:
```json
{
  "content": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "text": {"type": "string"},
      "metadata": {"type": "object"}
    },
    "required": ["text"]
  },
  "analysis_options": {
    "type": "object",
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
}
```

**Output Schema**:
```json
{
  "insights": {
    "type": "object",
    "properties": {
      "main_topics": {
        "type": "array",
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
        "properties": {
          "polarity": {"type": "number"},
          "subjectivity": {"type": "number"},
          "label": {"type": "string"}
        }
      }
    }
  },
  "analysis_metadata": {
    "type": "object",
    "properties": {
      "processing_time": {"type": "number"},
      "confidence_score": {"type": "number"},
      "language_detected": {"type": "string"}
    }
  }
}
```

### 3. generate_quadrant_analysis

**Purpose**: Generate 2x2 quadrant analysis with SVG visualization based on article insights.

**Value Proposition**: Creates visual quadrant analysis that highlights key insights and relationships in article content.

**Input Schema**:
```json
{
  "insights": {
    "type": "object",
    "description": "Analysis results from analyze_article_insights"
  },
  "quadrant_config": {
    "type": "object",
    "properties": {
      "x_axis": {
        "type": "object",
        "properties": {
          "label": {"type": "string"},
          "min_label": {"type": "string"},
          "max_label": {"type": "string"},
          "dimension": {"type": "string", "enum": ["importance", "sentiment", "novelty", "practicality", "custom"]}
        }
      },
      "y_axis": {
        "type": "object",
        "properties": {
          "label": {"type": "string"},
          "min_label": {"type": "string"},
          "max_label": {"type": "string"},
          "dimension": {"type": "string", "enum": ["urgency", "impact", "feasibility", "complexity", "custom"]}
        }
      },
      "quadrant_labels": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Labels for Q1, Q2, Q3, Q4"
      }
    },
    "required": ["x_axis", "y_axis"]
  },
  "visualization_options": {
    "type": "object",
    "properties": {
      "width": {"type": "integer", "default": 500},
      "height": {"type": "integer", "default": 500},
      "color_scheme": {"type": "string", "default": "professional"},
      "show_legend": {"type": "boolean", "default": true},
      "show_grid": {"type": "boolean", "default": true}
    }
  }
}
```

**Output Schema**:
```json
{
  "quadrant_analysis": {
    "type": "object",
    "properties": {
      "svg_content": {
        "type": "string",
        "description": "SVG visualization content"
      },
      "quadrants": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "quadrant": {"type": "string"},
            "label": {"type": "string"},
            "insights": {
              "type": "array",
              "items": {"type": "object"}
            },
            "count": {"type": "integer"}
          }
        }
      },
      "summary": {
        "type": "object",
        "properties": {
          "total_insights": {"type": "integer"},
          "dominant_quadrant": {"type": "string"},
          "analysis_title": {"type": "string"}
        }
      }
    }
  },
  "metadata": {
    "type": "object",
    "properties": {
      "generated_at": {"type": "string"},
      "config_used": {"type": "object"},
      "confidence_score": {"type": "number"}
    }
  }
}
```

### 4. create_custom_quadrant

**Purpose**: Create custom quadrant analysis with user-defined parameters and manual insight placement.

**Value Proposition**: Allows users to create tailored quadrant analyses with specific criteria and manual control.

**Input Schema**:
```json
{
  "title": {"type": "string"},
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
        "x_position": {"type": "number"},
        "y_position": {"type": "number"},
        "quadrant": {"type": "string"},
        "weight": {"type": "number", "default": 1.0}
      },
      "required": ["content"]
    }
  },
  "styling": {
    "type": "object",
    "properties": {
      "color_scheme": {"type": "string"},
      "font_size": {"type": "integer"},
      "show_labels": {"type": "boolean"}
    }
  }
}
```

## Tool Interdependencies and Workflows

### Primary Workflow
1. **extract_article_content** → Get clean content
2. **analyze_article_insights** → Extract structured insights
3. **generate_quadrant_analysis** → Create visual analysis

### Alternative Workflows
1. **Direct Analysis**: Users can provide pre-analyzed insights directly to **generate_quadrant_analysis**
2. **Custom Analysis**: Users can use **create_custom_quadrant** for manual quadrant creation
3. **Preview Mode**: Use **preview_analysis** before full processing

### Data Flow
```
Content Source → Extract Content → Analyze Insights → Generate Quadrant → Export Results
     ↓               ↓              ↓               ↓              ↓
   Validation    Cleaning      Classification   Visualization   Multiple Formats
```

## Error Handling Strategies

### Common Error Patterns
1. **Content Access Errors**
   - Network timeouts
   - File permission issues
   - Invalid URLs
   - Paywall restrictions

2. **Analysis Errors**
   - Content too short
   - Unsupported language
   - Processing timeouts
   - Memory constraints

3. **Visualization Errors**
   - Invalid quadrant configuration
   - Too many insights for display
   - SVG generation failures
   - Styling conflicts

### Error Recovery Mechanisms
1. **Graceful Degradation**: Continue processing with partial results
2. **Retry Logic**: Automatic retry for transient failures
3. **User Guidance**: Clear error messages with suggested actions
4. **Fallback Options**: Alternative processing methods

## Performance Considerations

### Optimization Strategies
1. **Async Processing**: Non-blocking I/O for network operations
2. **Content Caching**: Cache extracted content for re-use
3. **Batch Processing**: Process multiple insights efficiently
4. **Memory Management**: Stream processing for large articles

### Resource Limits
1. **Content Size**: Maximum 50,000 characters per article
2. **Processing Time**: 60-second timeout per operation
3. **Memory Usage**: 512MB maximum per analysis
4. **Concurrent Requests**: Limit to 5 simultaneous analyses

## Testing and Validation

### Unit Testing
- Individual tool functionality
- Input validation
- Error handling
- Output format compliance

### Integration Testing
- End-to-end workflows
- Tool interdependencies
- Performance benchmarks
- Error recovery scenarios

### User Acceptance Testing
- Real-world article analysis
- Visualization quality
- Error message clarity
- Overall user experience

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Extended language capabilities
2. **Advanced NLP**: More sophisticated analysis models
3. **Custom Templates**: User-defined quadrant templates
4. **Collaboration**: Shared analysis and commenting
5. **API Integration**: External data source connections

### Technical Improvements
1. **Machine Learning**: Custom classification models
2. **Real-time Updates**: Dynamic content refresh
3. **Mobile Support**: Responsive visualizations
4. **Export Options**: Additional format support
