"""Unit tests for MCP server tool functions.

Tests call the tool functions directly (they are plain Python functions).
The MCP server module is wired with the test service via set_service().
"""

import pytest

import docent.adapters.mcp_server.server as mcp_module
from docent.application.service import PortfolioService


@pytest.fixture(autouse=True)
def wired_service(service: PortfolioService):
    """Wire the test service into the MCP server module for each test."""
    mcp_module.set_service(service)
    yield
    mcp_module._service = None


def test_run_scenario_returns_result() -> None:
    result = mcp_module.run_scenario("base")
    assert "outputs" in result
    assert result["scenario_name"] == "base"


def test_run_scenario_with_override() -> None:
    result = mcp_module.run_scenario("base", overrides={"rate": 6.0})
    assert result["outputs"]["value"] == pytest.approx(93.5)


def test_run_scenario_unknown_returns_error() -> None:
    result = mcp_module.run_scenario("unknown")
    assert "error" in result


def test_override_input_returns_confirmation() -> None:
    result = mcp_module.override_input("rates", "rate", 6.0)
    assert "message" in result
    assert result["value"] == 6.0
    assert result["field"] == "rate"


def test_reset_overrides_returns_message() -> None:
    mcp_module.override_input("rates", "rate", 6.0)
    result = mcp_module.reset_overrides()
    assert "message" in result


def test_compare_scenarios_returns_differences() -> None:
    result = mcp_module.compare_scenarios("base", "stress")
    assert "differences" in result
    assert "value" in result["differences"]


def test_get_available_scenarios_lists_all() -> None:
    result = mcp_module.get_available_scenarios()
    assert "scenarios" in result
    names = {s["name"] for s in result["scenarios"]}
    assert "base" in names
    assert "stress" in names


def test_tools_return_error_when_no_service() -> None:
    mcp_module._service = None
    result = mcp_module.run_scenario("base")
    assert "error" in result
