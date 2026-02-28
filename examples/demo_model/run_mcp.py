"""Start the MCP server wired to the demo bond portfolio model.

Run with:
    uv run mcp dev examples/demo_model/run_mcp.py

Or via the docent-mcp entry point:
    docent-mcp examples.demo_model.model:build_service

Then connect Claude Desktop using claude_desktop_config.json.example.
"""

import docent

from model import build_service

service = build_service()

if __name__ == "__main__":
    docent.run_mcp(service)
