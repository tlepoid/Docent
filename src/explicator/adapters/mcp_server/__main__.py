"""Entry point: python -m explicator.adapters.mcp_server [module:attribute]."""

import sys

import explicator


def main() -> None:
    """Start the MCP server.

    Accepts an optional service path argument::

        python -m explicator.adapters.mcp_server myapp.model:build_service

    Falls back to stub wiring if no path is given.
    """
    if len(sys.argv) > 1:
        service = explicator.load_service(sys.argv[1])
    else:
        from explicator.adapters.data.in_memory import _build_stub_wiring
        from explicator.application.service import ModelService

        repository, runner = _build_stub_wiring()
        service = ModelService(runner=runner, repository=repository)

    explicator.run_mcp(service)


main()
