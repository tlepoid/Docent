"""Start the MCP server wired to the demo bond portfolio model.

Run with:
    uv run mcp dev examples/demo_model/run_mcp.py

Or via the explicator-mcp entry point:
    explicator-mcp examples.demo_model.model:build_service

Then connect Claude Desktop using claude_desktop_config.json.example.
"""

from explicator.adapters.mcp_server.server import mcp, set_service

from model import build_service

service = build_service()
set_service(service)

if __name__ == "__main__":
    mcp.run()
