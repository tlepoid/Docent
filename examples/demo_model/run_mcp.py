"""Start the MCP server wired to the demo bond portfolio model.

Run with:
    python examples/demo_model/run_mcp.py

Then connect Claude Desktop using claude_desktop_config.json.example.
"""

from docent.adapters.mcp_server.server import mcp, set_service
from docent.application.service import PortfolioService

from model import build_repository, build_runner

if __name__ == "__main__":
    repository = build_repository()
    runner = build_runner()
    service = PortfolioService(runner=runner, repository=repository)
    set_service(service)
    mcp.run()
