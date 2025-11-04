# 🚀 Quick Start Guide

Get your Article Quadrant Analyzer MCP server running in 5 minutes!

## ⚡ 5-Minute Deployment

### 1. Deploy to Your IDE

```bash
# For Cursor
./deploy_to_ide_standard.sh cursor

# For VS Code
./deploy_to_ide_standard.sh vscode

# For Claude Desktop
./deploy_to_ide_standard.sh claude
```

### 2. Restart Your IDE

- **Cursor**: Restart the application
- **VS Code**: Reload window (Cmd+R) or restart
- **Claude Desktop**: Restart the application

### 3. Start Using!

Ask your AI assistant:
```
"Please analyze this article and create a quadrant analysis: [paste article text or URL]"
```

## 🔧 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Install FastMCP
pip install fastmcp

# Start MCP Inspector for testing
fastmcp dev test_simple_server.py

# Opens: http://127.0.0.1:6274
```

## ✅ Verify Installation

```bash
# Validate MCP configuration
./deploy_to_ide_standard.sh validate
```

Expected output:
```
✅ MCP服务器配置验证通过
Components
  Tools:        3
  Prompts:      0
  Resources:    0
```

## 🎯 First Test

Try this simple test:

```
Extract key insights from this article about renewable energy trends and create a 2x2 quadrant analysis showing market maturity vs adoption rate.
```

## 🆘 Troubleshooting

### Server Not Found
- Check the file path in your IDE's MCP configuration
- Ensure FastMCP is installed: `pip install fastmcp`

### Permission Issues
- Make the deployment script executable: `chmod +x deploy_to_ide_standard.sh`

### Configuration Errors
- Run validation: `./deploy_to_ide_standard.sh validate`
- Check all paths in `config/` files are correct

## 📞 Need Help?

- Check [README.md](README.md) for detailed documentation
- Review [Configuration.md](CONFIGURATION.md) for advanced setup
- All technical specs in `.trae/specs/article-quadrant-analyzer/`

**🎉 You're ready to analyze articles with professional quadrant visualizations!**