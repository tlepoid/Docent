"""Entry point: python -m docent.adapters.mcp_server [module:attribute]."""

import sys

import docent


def main() -> None:
    """Start the MCP server.

    Accepts an optional service path argument::

        python -m docent.adapters.mcp_server myapp.model:build_service

    Falls back to stub wiring if no path is given.
    """
    if len(sys.argv) > 1:
        service = docent.load_service(sys.argv[1])
    else:
        from docent.adapters.data.in_memory import _build_stub_wiring
        from docent.application.service import ModelService

        repository, runner = _build_stub_wiring()
        service = ModelService(runner=runner, repository=repository)

    docent.run_mcp(service)


main()
