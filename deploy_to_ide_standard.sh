#!/bin/bash

# 文章四象限分析MCP服务器 - 标准MCP部署脚本
# 使用方法: ./deploy_to_ide_standard.sh [ide名称]

set -e

IDE=${1:-"help"}
PROJECT_DIR="/Users/vincent/Library/CloudStorage/SynologyDrive-vincent/My.create/Developer/MCP"

echo "🚀 文章四象限分析MCP服务器部署 (标准MCP格式)"
echo "============================================="

case $IDE in
    "cursor")
        echo "📱 部署到 Cursor (标准MCP格式)..."
        if command -v fastmcp &> /dev/null; then
            cd "$PROJECT_DIR"
            fastmcp install cursor test_simple_server.py
            echo "✅ 已安装到Cursor，请重启Cursor应用"
        else
            echo "❌ 未找到fastmcp，请先安装: pip install fastmcp"
            exit 1
        fi
        ;;

    "vscode")
        echo "💻 部署到 VS Code (标准MCP格式)..."
        if command -v fastmcp &> /dev/null; then
            cd "$PROJECT_DIR"
            fastmcp install claude-code test_simple_server.py
            echo "✅ 已安装到VS Code，请确保安装了Claude Code扩展"
        else
            echo "❌ 未找到fastmcp，请先安装: pip install fastmcp"
            exit 1
        fi
        ;;

    "claude-desktop")
        echo "🖥️ 部署到 Claude Desktop (标准MCP格式)..."
        if command -v fastmcp &> /dev/null; then
            cd "$PROJECT_DIR"
            fastmcp install claude-desktop test_simple_server.py
            echo "✅ 已安装到Claude Desktop，请重启应用"
        else
            echo "❌ 未找到fastmcp，请先安装: pip install fastmcp"
            exit 1
        fi
        ;;

    "manual-cursor")
        echo "📝 生成Cursor手动配置 (标准MCP格式)..."
        echo "请将以下内容添加到Cursor设置中:"
        echo "文件位置: ~/Library/Application Support/Cursor/User/settings.json"
        echo ""
        cat "$PROJECT_DIR/config_cursor_standard.json"
        ;;

    "manual-vscode")
        echo "📝 生成VS Code手动配置 (标准MCP格式)..."
        echo "请将以下内容添加到VS Code settings.json中:"
        echo ""
        cat "$PROJECT_DIR/config_vscode_standard.json"
        ;;

    "http")
        echo "🌐 启动HTTP服务器模式..."
        cd "$PROJECT_DIR"
        echo "启动HTTP服务器在 http://localhost:8000/mcp"
        echo "按Ctrl+C停止服务器"
        uvx --quiet --python 3.12 --with fastmcp python -c "
import asyncio
from test_simple_server import mcp
print('🚀 启动HTTP服务器...')
mcp.run(transport='http', host='127.0.0.1', port=8000)
"
        ;;

    "validate")
        echo "🔍 验证MCP配置..."
        cd "$PROJECT_DIR"
        if command -v fastmcp &> /dev/null; then
            fastmcp inspect test_simple_server.py
            echo "✅ MCP服务器配置验证通过"
        else
            echo "❌ 未找到fastmcp，无法验证配置"
            exit 1
        fi
        ;;

    "help"|"-h"|"--help")
        echo "使用方法: $0 [ide名称]"
        echo ""
        echo "支持的IDE:"
        echo "  cursor         - 自动安装到Cursor (推荐)"
        echo "  vscode         - 自动安装到VS Code"
        echo "  claude-desktop - 自动安装到Claude Desktop"
        echo "  manual-cursor  - 生成Cursor手动配置"
        echo "  manual-vscode  - 生成VS Code手动配置"
        echo "  http           - 启动HTTP服务器模式"
        echo "  validate       - 验证MCP配置"
        echo "  help           - 显示此帮助信息"
        echo ""
        echo "注意: 所有配置都符合MCP标准协议，不包含非标准字段"
        ;;

    *)
        echo "❌ 不支持的IDE: $IDE"
        echo "支持的IDE: cursor, vscode, claude-desktop, manual-cursor, manual-vscode, http, validate"
        echo "使用 '$0 help' 查看详细帮助"
        exit 1
        ;;
esac

echo ""
echo "🎉 部署完成！"
echo "📚 所有配置都符合MCP标准协议"
echo "📖 更多信息请查看: IDE_INTEGRATION_GUIDE.md"
