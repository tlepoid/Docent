"""Unit tests for ToolDispatcher."""

import pytest

from docent.ai.dispatcher import ToolDispatcher
from docent.application.service import PortfolioService


@pytest.fixture
def dispatcher(service: PortfolioService) -> ToolDispatcher:
    return ToolDispatcher(service)


def test_dispatch_run_scenario(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch("run_scenario", {"name": "base"})
    assert "outputs" in result
    assert result["scenario_name"] == "base"


def test_dispatch_run_scenario_with_overrides(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch("run_scenario", {"name": "base", "overrides": {"rate": 6.0}})
    assert result["outputs"]["value"] == pytest.approx(93.5)


def test_dispatch_override_input(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch(
        "override_input", {"source": "rates", "field": "rate", "value": 6.0}
    )
    assert "message" in result
    assert result["value"] == 6.0


def test_dispatch_reset_overrides(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch("reset_overrides", {})
    assert "message" in result


def test_dispatch_compare_scenarios(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch(
        "compare_scenarios", {"scenario_a": "base", "scenario_b": "stress"}
    )
    assert "differences" in result
    assert "value" in result["differences"]


def test_dispatch_get_available_scenarios(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch("get_available_scenarios", {})
    assert "scenarios" in result
    assert len(result["scenarios"]) == 2


def test_dispatch_unknown_tool_returns_error(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch("nonexistent_tool", {})
    assert "error" in result
    assert "Unknown tool" in result["error"]


def test_dispatch_handles_service_exception(dispatcher: ToolDispatcher) -> None:
    result = dispatcher.dispatch("run_scenario", {"name": "does_not_exist"})
    assert "error" in result


def test_dispatch_never_raises(dispatcher: ToolDispatcher) -> None:
    # Should always return a dict, never raise
    result = dispatcher.dispatch("run_scenario", {})  # missing required arg
    assert isinstance(result, dict)
    assert "error" in result
