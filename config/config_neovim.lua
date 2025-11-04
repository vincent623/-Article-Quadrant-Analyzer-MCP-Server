
-- Neovim MCP配置
require("mcp").setup({
  servers = {
    article_quadrant_analyzer = {
      command = "uvx",
      args = {"--quiet", "--python", "3.12", "--with", "fastmcp", "python", "test_simple_server.py"},
      cwd = "/Users/vincent/Library/CloudStorage/SynologyDrive-vincent/My.create/Developer/MCP/mcp-server-article-quadrant",
      env = {LOG_LEVEL = "INFO"}
    }
  }
})
