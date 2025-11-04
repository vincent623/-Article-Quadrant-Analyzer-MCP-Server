# 📊 Article Quadrant Analyzer MCP Server (Enhanced)

A powerful Model Context Protocol (MCP) server that extracts core insights from articles and generates intelligent Chinese quadrant analysis with direct text matrix visualization.

## ✨ Features

- **Multi-Source Content Processing**: URLs, files, screenshots (OCR), and direct text
- **Professional OCR**: Integration with Mistral Document AI API for high-accuracy screenshot analysis
- **2x2 Quadrant Analysis**: Automatic generation of insightful quadrant visualizations
- **SVG Output**: High-quality, scalable quadrant graphics
- **Agent-Centric Design**: Optimized for AI agent workflows
- **UVX Deployment**: Zero-dependency deployment for minimal cost

## 🚀 Quick Start

### 1. Fast Deployment (5 minutes)

```bash
# Deploy to Cursor
./deploy_to_ide_standard.sh cursor

# Deploy to VS Code
./deploy_to_ide_standard.sh vscode

# Deploy to Claude Desktop
./deploy_to_ide_standard.sh claude

# Validate deployment
./deploy_to_ide_standard.sh validate
```

### 2. Manual Setup

```bash
# Install dependencies
uvx --quiet --python 3.12 --with fastmcp python test_simple_server.py

# Start MCP Inspector for testing
fastmcp dev test_simple_server.py
```

## 📁 Project Structure

```
mcp-server-article-quadrant/
├── test_simple_server.py              # Main MCP server (3 tools)
├── deploy_to_ide_standard.sh          # Automated deployment script
├── config/                            # IDE configurations
│   ├── config_cursor_standard.json
│   ├── config_vscode_standard.json
│   ├── config_claude_desktop_standard.json
│   ├── config_emacs.el
│   └── config_neovim.lua
├── src/mcp_server_article_quadrant/   # Modular source code
│   ├── server.py                      # FastMCP server setup
│   ├── tools/                         # MCP tools
│   │   ├── extract_content.py
│   │   ├── analyze_insights.py
│   │   └── generate_quadrant.py
│   ├── models/                        # Pydantic models
│   │   ├── content.py
│   │   ├── analysis.py
│   │   └── quadrant.py
│   └── utils/                         # Utilities
│       ├── content_extractor.py
│       ├── quadrant_generator.py
│       └── image_processor.py
├── .trae/specs/article-quadrant-analyzer/  # Technical specifications
│   ├── spec.md (24KB)                 # Complete MCP server specification
│   └── api-research.md (25KB)         # API research and content sources
├── pyproject.toml                     # Project configuration
├── .env.example                       # Environment variables template
├── 2X2分析prompt.md                   # Original analysis prompt
└── DOCUMENTATION_SUMMARY.md           # Documentation cleanup summary
```

## 🔧 Configuration

### Environment Variables

```bash
# Mistral Document AI API (for OCR)
MISTRAL_API_KEY=your_api_key_here

# Content Processing
CONTENT_MAX_LENGTH=50000
OCR_MAX_FILE_SIZE=10485760
```

### IDE Configuration Examples

**Cursor:**
```json
{
  "mcpServers": {
    "article-quadrant-analyzer": {
      "command": "uvx",
      "args": [
        "--quiet", "--python", "3.12", "--with", "fastmcp",
        "python", "/Users/vincent/Library/CloudStorage/SynologyDrive-vincent/My.create/Developer/MCP/test_simple_server.py"
      ]
    }
  }
}
```

More configuration examples in `config/` directory.

## 🛠️ MCP Tools

### 1. `extract_article_content_simple`
**Enhanced content extraction with AI-friendly interface**

**Intelligent Processing:**
- Automatic HTML/XML tag removal
- Language detection (Chinese/English/Mixed)
- Content quality analysis
- URL and format detection
- Comprehensive metrics (characters, words, sentences, paragraphs)

**Universal Input Support:**
- URLs (news websites, WeChat public accounts)
- Text files and documents
- Direct text input
- OCR processed content
- Mixed-format content

**Smart Output:**
- Content preview with truncation
- Complexity assessment
- Processing recommendations
- Next-step guidance

### 2. `analyze_article_insights_simple`
**Advanced content insights extraction**

**Keyword Analysis:**
- Frequency-based keyword extraction
- Topic identification and clustering
- Content summarization
- Trend detection

**Intelligence Features:**
- Automatic topic categorization
- Insight relevance scoring
- Content structure analysis
- Actionable insight generation

### 3. `generate_quadrant_analysis_simple`
**Enhanced Chinese quadrant analysis engine**

**Smart Content Processing:**
- Intelligent Chinese language detection and analysis
- Context-aware content preprocessing
- Flexible axis labeling (supports Chinese labels)
- Robust error handling and parameter validation

**Advanced Classification Logic:**
- **Collaboration Analysis**: Detects team work, coordination, and group activities
- **Textual Analysis**: Identifies documentation, writing, and formal communication
- **Pattern Recognition**: Maps content to appropriate quadrants based on actual text patterns
- **Chinese Context Support**: Specifically trained for Chinese business and work scenarios

**Direct Matrix Output:**
- **Real-time ASCII Visualization**: Matrix appears directly in dialogue
- **Chinese Quadrant Names**: 重点投入区, 专业分析区, 基础维护区, 创意协作区
- **Content-Specific Mapping**: Analyzes your actual content for accurate placement
- **No Conversion Needed**: Instant results without SVG/PNG conversion steps

**Rich Output Format:**
- Professional quadrant mapping
- Detailed content metrics
- Strategic insights and recommendations
- **Direct text matrix visualization** (Chinese)
- **Smart content classification** based on actual text analysis

**AI-Friendly Features:**
- Automatic XML/HTML tag cleanup
- Flexible parameter format support
- Comprehensive error handling
- Context-aware response generation
- **Chinese language support** with intelligent content analysis

**🎨 Enhanced Visualization Capabilities:**
- **Intelligent Text Matrix**: Direct ASCII quadrant display in dialogue
- **Chinese Content Analysis**: Smart classification based on collaboration vs text levels
- **Context-Aware Mapping**: Analyzes content patterns for accurate quadrant placement
- **Real-time Results**: No SVG conversion needed - matrix appears immediately
- **Dynamic Naming**: Quadrants named in Chinese (重点投入区, 专业分析区, 基础维护区, 创意协作区)

## 📋 Supported Content Sources

- **News Websites**: Major news platforms and online publications
- **WeChat Public Accounts**: Articles from WeChat official accounts
- **Screenshots**: OCR processing via Mistral Document AI API
- **Text Files**: Direct file content extraction
- **Direct Input**: Manual text entry for analysis

## 🎯 Use Cases

- **Work Process Analysis**: Analyze team collaboration workflows and documentation patterns
- **Project Management**: Visualize task distribution and work flow efficiency
- **Team Coordination**: Identify collaboration bottlenecks and optimization opportunities
- **Content Strategy**: Map content types across collaboration and formality dimensions
- **Decision Making**: Framework for resource allocation and task prioritization

## 📊 Sample Output

**Input:**
```
工作的流动性: 没有任何一个岗位只存在于一个象限...
例如开发新功能: 团队头脑风暴，撰写PRD文档，工程师独立编写代码...
```

**Direct Matrix Output:**
```
🎯 四象限矩阵图

                    ↑ 文本化程度 ↑
                    ┌──────────────────────────────┐
                    │     Q1: 重点投入区     │
                    │  ┌────────────────────────┐  │
                    │  │ • 团队协作文档      │  │
                    │  │ • 集体讨论记录      │  │
                    │  │ • 共享成果展示      │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐
                    │     Q2: 专业分析区     │
                    │  ┌────────────────────────┐  │
                    │  │ • 独立深度思考      │  │
                    │  │ • 个人专业分析      │  │
                    │  │ • 核心技术实现      │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
← 协作程度 ← ─────────────────────────────────── → 协作程度 →
                    ┌──────────────────────────────┐
                    │     Q3: 基础维护区     │
                    │  ┌────────────────────────┐  │
                    │  │ • 基础维护工作      │  │
                    │  │ • 常规操作流程      │  │
                    │  │ • 标准规范执行      │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐
                    │     Q4: 创意协作区     │
                    │  ┌────────────────────────┐  │
                    │  │ • 创意头脑风暴      │  │
                    │  │ • 视觉化表达        │  │
                    │  │ • 互动协作展示      │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
```

## 🔍 Testing & Validation

```bash
# Test MCP Inspector
fastmcp dev test_simple_server.py
# Opens: http://127.0.0.1:6274

# Validate UVX deployment
./deploy_to_ide_standard.sh validate

# Test individual tools via MCP Inspector interface
```

## 📚 Documentation

- **[Technical Specification](.trae/specs/article-quadrant-analyzer/spec.md)** - Complete MCP server design (24KB)
- **[API Research](.trae/specs/article-quadrant-analyzer/api-research.md)** - Content source analysis (25KB)
- **[Documentation Summary](DOCUMENTATION_SUMMARY.md)** - Project organization and cleanup history

## ⚡ Performance

- **Startup Time**: <2 seconds with UVX
- **Memory Usage**: ~50MB baseline
- **Processing**: 1-5 seconds for typical articles
- **OCR Processing**: 3-10 seconds via Mistral API

## 🎨 Generated Output Examples

The server generates professional quadrant analyses in SVG format showing:
- **Strategic Positioning**: Content mapped across two axes
- **Visual Clarity**: Clean, professional quadrants with labels
- **Actionable Insights**: Recommendations based on positioning
- **Contextual Analysis**: Tailored to content type and goals

---

**🚀 Ready to transform your article analysis workflow!**

*Generated with FastMCP Spec-Driven Development Guide*