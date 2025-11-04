# API Research - Article Quadrant Analyzer MCP Server

## Overview
This document outlines the research for creating an MCP server that performs 2x2 quadrant analysis on article content. The server will extract key insights from articles and generate visual quadrant analysis using SVG graphics.

## Core Functionality Requirements

### 1. Content Input Methods
The server needs to support multiple content input sources:

**URL-based Content:**
- Web scraping capabilities to extract article content from URLs
- Support for common news sites, blogs, and academic platforms
- HTML parsing and content cleaning
- Handle paywalls and access restrictions gracefully

**Special URL Sources - News Websites:**
- Support for major news platforms (CNN, BBC, Reuters, 新华网, 人民网, etc.)
- Handle news article structure (headline, byline, timestamp, body)
- Extract metadata like publication date, author, category
- Deal with paywall content and subscription requirements

**Special URL Sources - WeChat Public Accounts (公众号):**
- Extract content from WeChat public account articles
- Handle WeChat-specific HTML structure and formatting
- Process embedded media and special formatting
- Extract author information and publication data
- Handle authentication requirements for some articles

**File-based Content:**
- Local file reading (PDF, TXT, MD, DOCX)
- **Image Files**: PNG, JPG, JPEG, WEBP for screenshots
- File path validation and security checks
- Support for various document formats

**Screenshot/Image Content:**
- OCR (Optical Character Recognition) for extracting text from images
- Support for news screenshots, article screenshots, social media posts
- Handle different image qualities and resolutions
- Text cleaning and formatting after OCR extraction

**Direct Text Input:**
- Direct text content input
- String validation and processing
- Support for multiple languages and character encodings

### 2. Text Analysis Capabilities

**Content Extraction:**
- Main content identification and extraction
- Remove navigation, ads, and irrelevant content
- Title and metadata extraction
- Author and publication date identification

**Key Insight Extraction:**
- Topic modeling and keyword extraction
- Sentiment analysis
- Entity recognition
- Key phrase and concept identification
- Argument and claim extraction

**Quadrant Analysis Logic:**
- Two-dimensional classification system
- Customizable axis dimensions
- Automatic quadrant assignment based on analysis
- Confidence scoring for classifications

### 3. SVG Generation Requirements

**Visual Elements:**
- Coordinate system with axes and arrows
- Customizable axis labels and scales
- Quadrant content positioning
- Legend and explanatory text
- Responsive sizing and scaling

**Styling and Formatting:**
- Consistent color schemes
- Font sizing and readability
- Professional appearance
- Accessibility considerations

## Technical Implementation Considerations

### 1. FastMCP Framework Integration
- Leverage FastMCP's tool definition capabilities
- Use Python async/await patterns
- Implement proper error handling and validation
- Support for streaming responses for long articles

### 2. Text Processing Libraries
**Candidate Libraries:**
- `newspaper3k` or `readability-lxml` for web content extraction
- `nltk` or `spaCy` for natural language processing
- `transformers` (Hugging Face) for advanced NLP
- `beautifulsoup4` for HTML parsing
- `pypdf` or `pdfplumber` for PDF processing

**OCR Libraries for Image/Screenshot Processing:**
- **Primary**: `Mistral Document AI API` (https://api.mistral.ai) for professional OCR
  - High accuracy for Chinese and English text
  - Handles complex layouts and formatting
  - Cloud-based processing (no local GPU requirements)
  - Structured data extraction capabilities
- **Fallback**: `pytesseract` or `easyocr` for offline processing
- `Pillow` (PIL) for image preprocessing
- `imageio` for image file handling

**WeChat-Specific Handling:**
- Custom parsers for WeChat HTML structure
- WeChat API integration (if available)
- WeChat content cleaning utilities

### 3. Analysis Algorithms
**Content Analysis Approach:**
- TF-IDF for keyword extraction
- Named Entity Recognition (NER)
- Sentiment analysis using pre-trained models
- Topic modeling (LDA or similar)
- Text similarity and clustering

**Quadrant Classification:**
- Rule-based classification system
- Machine learning models for automatic classification
- Confidence scoring mechanisms
- Manual override capabilities

### 4. Performance and Scalability
- Async processing for large articles
- Caching for frequently accessed URLs
- Rate limiting for web requests
- Memory management for large documents

## Constraints and Limitations

### 1. Content Access Restrictions
- Paywall content may not be accessible
- Some websites block scraping attempts
- Regional content restrictions
- Authentication requirements

### 2. Source-Specific Challenges
**News Website Limitations:**
- Dynamic content loading (JavaScript-heavy sites)
- Anti-bot detection and rate limiting
- Paywall detection and handling
- Real-time content updates

**WeChat Public Account Limitations:**
- WeChat anti-scraping mechanisms
- Authentication requirements for certain content
- Special formatting challenges
- Potential content restrictions

**Screenshot/Image Processing Limitations:**
- **Mistral API dependency**: Requires API key and internet connection
- API rate limits and cost considerations
- Image size and format restrictions
- Processing latency for API calls
- **Fallback OCR accuracy** for offline processing
- Handwriting or highly stylized fonts may still be challenging

### 3. Language Support
- Primary focus on Chinese and English content
- Limited support for other languages
- Translation requirements for multilingual content
- OCR accuracy for Chinese characters in images

### 4. Analysis Accuracy
- AI-based analysis may have interpretation errors
- Context understanding limitations
- Bias in classification models
- Need for human validation
- **High-quality OCR accuracy with Mistral API** for image content
- Fallback OCR limitations when API is unavailable

### 5. Technical Constraints
- Rate limiting on web requests
- File size limitations
- Processing time for long documents
- Memory constraints for large content
- **Mistral API rate limits and quota management**
- **API call latency and timeout handling**
- Cost management for API usage
- Fallback mechanisms for offline processing

## Data Privacy and Security

### 1. Content Handling
- No persistent storage of user content
- Secure handling of sensitive information
- Compliance with data protection regulations
- Clear data retention policies

### 2. URL Security
- Validation of URL formats
- Prevention of malicious URL processing
- Network security considerations
- Timeout and resource limits

### 3. API Security (Mistral Document AI)
- Secure API key management using environment variables
- No logging of sensitive content or API keys
- Rate limiting and quota monitoring
- Fallback to offline OCR when API is unavailable
- Compliance with Mistral's data processing policies

## Integration Requirements

### 1. Claude Desktop Integration
- STDIO transport protocol for local development
- Simple configuration and setup
- Efficient context management
- Error reporting and debugging support

### 2. Output Formats
- SVG graphics for visual representation
- JSON metadata for programmatic access
- Markdown documentation for human readability
- Structured error messages

## Success Criteria

### 1. Functional Requirements
- [ ] Successfully extract content from URLs, files, and direct text
- [ ] **High-accuracy OCR using Mistral Document AI API**
- [ ] **Fallback OCR capabilities for offline processing**
- [ ] Generate meaningful 2x2 quadrant analyses
- [ ] Produce high-quality SVG visualizations
- [ ] Handle various content types and sources (news, WeChat, screenshots)

### 2. Quality Requirements
- [ ] Accurate content extraction (>90% success rate)
- [ ] **OCR accuracy >95% for clear images using Mistral API**
- [ ] Meaningful quadrant classifications
- [ ] Professional-looking visual outputs
- [ ] Robust error handling and API fallback mechanisms

### 3. Performance Requirements
- [ ] Process average article in <30 seconds
- [ ] **OCR processing time <10 seconds (API dependent)**
- [ ] Handle articles up to 10,000 words
- [ ] Support concurrent processing
- [ ] Minimal memory footprint
- [ ] **Cost-effective API usage with intelligent caching**

## Next Steps

1. Prototype basic content extraction from URLs
2. **Integrate Mistral Document AI API for professional OCR**
3. **Implement fallback OCR for offline processing**
4. **Add WeChat public account content extraction**
5. **Add news website-specific parsing logic**
6. Implement simple quadrant analysis logic
7. Create SVG generation functionality
8. Develop comprehensive error handling with API fallback mechanisms
9. Optimize for Claude Desktop integration
10. Create comprehensive testing suite with diverse content sources
