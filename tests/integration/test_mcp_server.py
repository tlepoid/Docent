"""Integration tests: MCP server wiring and end-to-end tool execution."""

import pytest

import explicator.adapters.mcp_server.server as mcp_module
from explicator.adapters.mcp_server.server import mcp, set_service
from explicator.application.service import ModelService


@pytest.fixture(autouse=True)
def wired_mcp(service: ModelService) -> None:
    """Wire the test service into the MCP server for each test."""
    set_service(service)
    yield mcp
    mcp_module._service = None


def test_mcp_server_module_imports() -> None:
    """MCP server module should import and expose the FastMCP instance."""
    assert mcp is not None
    assert mcp.name == "Explicator"


def test_run_scenario_end_to_end() -> None:
    """Full round-trip: run a scenario and verify outputs are present."""
    result = mcp_module.run_scenario("base")
    assert isinstance(result, dict)
    assert "outputs" in result
    assert "scenario_name" in result
    assert result["scenario_name"] == "base"


def test_override_then_run_reflects_override() -> None:
    """Override an input, run a scenario, verify the override affected the result."""
    mcp_module.override_input("rates", "rate", 6.0)
    result = mcp_module.run_scenario("base")
    assert result["outputs"]["value"] == pytest.approx(93.5)


def test_reset_clears_overrides() -> None:
    """Test that reset_overrides restores default values."""
    mcp_module.override_input("rates", "rate", 6.0)
    mcp_module.reset_overrides()
    result = mcp_module.run_scenario("base")
    assert result["outputs"]["value"] == pytest.approx(100.0)


def test_compare_scenarios_end_to_end() -> None:
    """Test full round-trip comparison of two scenarios."""
    result = mcp_module.compare_scenarios("base", "stress")
    assert "differences" in result
    assert result["differences"]["value"]["delta"] == pytest.approx(-6.5)


def test_schema_resource_is_valid_json() -> None:
    """Test that the model schema resource returns valid JSON."""
    import json

    raw = mcp_module.get_model_schema()
    data = json.loads(raw)
    assert "name" in data
    assert "inputs" in data
    assert "outputs" in data


def test_overrides_resource_reflects_active_overrides() -> None:
    """Test that the overrides resource reflects currently active overrides."""
    import json

    mcp_module.override_input("rates", "rate", 6.0)
    raw = mcp_module.get_current_overrides()
    data = json.loads(raw)
    assert len(data) == 1
    assert data[0]["field"] == "rate"


def test_results_resource_reflects_latest_run() -> None:
    """Test that the results resource reflects the most recent scenario run."""
    import json

    mcp_module.run_scenario("base")
    raw = mcp_module.get_latest_results()
    data = json.loads(raw)
    assert "base" in data
