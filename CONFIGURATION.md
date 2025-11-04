# ⚙️ Configuration Reference

Complete guide for configuring your Article Quadrant Analyzer MCP server.

## 📋 Table of Contents

- [Environment Variables](#environment-variables)
- [IDE Configurations](#ide-configurations)
- [MCP Server Settings](#mcp-server-settings)
- [Content Processing Limits](#content-processing-limits)

## 🔧 Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Required: Mistral Document AI API for OCR functionality
MISTRAL_API_KEY=your_mistral_api_key_here

# Optional: Content processing limits
CONTENT_MAX_LENGTH=50000
OCR_MAX_FILE_SIZE=10485760

# Optional: Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Optional: HTTP timeout for content extraction
HTTP_TIMEOUT=30
```

### Getting Mistral API Key

1. Visit [Mistral AI Console](https://console.mistral.ai/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new API key
5. Add to your `.env` file

## 💻 IDE Configurations

### Cursor

**Location**: `~/.cursor/mcp_settings.json`

```json
{
  "mcpServers": {
    "article-quadrant-analyzer": {
      "command": "uvx",
      "args": [
        "--quiet",
        "--python",
        "3.12",
        "--with",
        "fastmcp",
        "python",
        "/absolute/path/to/test_simple_server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### VS Code

**Location**: `~/.vscode/mcp_settings.json`

```json
{
  "mcpServers": {
    "article-quadrant-analyzer": {
      "command": "uvx",
      "args": [
        "--quiet",
        "--python",
        "3.12",
        "--with",
        "fastmcp",
        "python",
        "/absolute/path/to/test_simple_server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Claude Desktop

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "article-quadrant-analyzer": {
      "command": "uvx",
      "args": [
        "--quiet",
        "--python",
        "3.12",
        "--with",
        "fastmcp",
        "python",
        "/absolute/path/to/test_simple_server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Emacs

**Location**: Add to your Emacs config

```elisp
;; In your init.el or config file
(with-eval-after-load 'mcp
  (mcp-register-server
   "article-quadrant-analyzer"
   :command "uvx"
   :args '("--quiet" "--python" "3.12" "--with" "fastmcp" "python" "/absolute/path/to/test_simple_server.py")
   :env '(("LOG_LEVEL" . "INFO"))))
```

### Neovim

**Location**: Add to your Neovim config

```lua
-- In your init.lua
require('mcp').setup({
  servers = {
    ['article-quadrant-analyzer'] = {
      command = 'uvx',
      args = {'--quiet', '--python', '3.12', '--with', 'fastmcp', 'python', '/absolute/path/to/test_simple_server.py'},
      env = { LOG_LEVEL = 'INFO' }
    }
  }
})
```

## ⚙️ MCP Server Settings

### Transport Protocols

The server supports both stdio and HTTP transport:

**Stdio (Recommended for IDEs)**:
- Default configuration
- Better performance for IDE integration
- Simpler setup

**HTTP (For web applications)**:
```bash
# Start HTTP server
fastmcp dev --transport http test_simple_server.py
# Runs on http://127.0.0.1:PORT
```

### UVX Configuration

UVX provides zero-dependency deployment:

```bash
# Standard UVX command
uvx --quiet --python 3.12 --with fastmcp python test_simple_server.py

# With specific FastMCP version
uvx --quiet --python 3.12 --with "fastmcp==2.13.0.2" python test_simple_server.py
```

## 📊 Content Processing Limits

### Default Limits

```python
# Maximum content length for text processing
CONTENT_MAX_LENGTH = 50000  # characters

# Maximum file size for OCR processing
OCR_MAX_FILE_SIZE = 10485760  # bytes (10MB)

# HTTP request timeout
HTTP_TIMEOUT = 30  # seconds
```

### Adjusting Limits

Modify these in your environment or code:

```bash
# For large documents
CONTENT_MAX_LENGTH=100000

# For high-resolution images
OCR_MAX_FILE_SIZE=20971520  # 20MB

# For slow websites
HTTP_TIMEOUT=60
```

## 🔍 Validation

### Test Configuration

```bash
# Validate MCP setup
./deploy_to_ide_standard.sh validate

# Test with MCP Inspector
fastmcp dev test_simple_server.py
# Opens: http://127.0.0.1:6274
```

### Common Issues

**Path Issues**:
- Use absolute paths in configuration
- Verify the `test_simple_server.py` file exists
- Check directory permissions

**Dependency Issues**:
```bash
# Install FastMCP
pip install fastmcp

# Install with UVX (recommended)
pip install uvx

# Verify installation
fastmcp --version
```

**API Key Issues**:
- Verify Mistral API key is valid
- Check `.env` file is in project root
- Ensure API key has required permissions

## 📝 Configuration Templates

Ready-to-use templates are available in the `config/` directory:

- `config_cursor_standard.json`
- `config_vscode_standard.json`
- `config_claude_desktop_standard.json`
- `config_emacs.el`
- `config_neovim.lua`

## 🚀 Advanced Configuration

### Custom Server Settings

Modify `test_simple_server.py` for advanced configuration:

```python
# Custom server name and description
@mcp.server("custom-name")
async def custom_server():
    pass

# Custom tool configurations
@mcp.tool
async def custom_tool(
    ctx: Context,
    input_param: str = Field(description="Custom parameter")
) -> str:
    # Custom implementation
    pass
```

### Performance Optimization

```bash
# Use UVX for faster startup
uvx --quiet --python 3.12 --with fastmcp python test_simple_server.py

# Enable caching
export CONTENT_CACHE_ENABLED=true

# Use HTTP transport for web apps
fastmcp dev --transport http test_simple_server.py
```

---

**📚 Need more help?**
- Check [README.md](README.md) for overview
- Try [QUICK_START.md](QUICK_START.md) for fast setup
- Review technical specs in `.trae/specs/`