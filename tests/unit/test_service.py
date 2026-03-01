"""Unit tests for ModelService."""

import pytest

from explicator.application.service import ModelService


def test_get_available_scenarios(service: ModelService) -> None:
    """Test get available scenarios."""
    scenarios = service.get_available_scenarios()
    assert len(scenarios) == 2
    names = {s.name for s in scenarios}
    assert names == {"base", "stress"}


def test_run_scenario_base(service: ModelService) -> None:
    """Test run scenario base."""
    result = service.run_scenario("base")
    assert result.scenario_name == "base"
    assert result.outputs["value"] == pytest.approx(100.0)


def test_run_scenario_stress(service: ModelService) -> None:
    """Test run scenario stress."""
    result = service.run_scenario("stress")
    # stress overrides rate=6.0 → value = 100 - (6-5)*6.5 = 93.5
    assert result.outputs["value"] == pytest.approx(93.5)


def test_run_scenario_unknown_raises(service: ModelService) -> None:
    """Test run scenario unknown raises."""
    with pytest.raises(ValueError, match="Unknown scenario"):
        service.run_scenario("nonexistent")


def test_override_input_persists(service: ModelService) -> None:
    """Test override input persists."""
    service.override_input("rates", "rate", 6.0)
    result = service.run_scenario("base")
    assert result.outputs["value"] == pytest.approx(93.5)


def test_call_override_takes_precedence_over_session(service: ModelService) -> None:
    """Test call override takes precedence over session."""
    service.override_input("rates", "rate", 6.0)
    result = service.run_scenario("base", overrides={"rate": 7.0})
    # rate=7.0 wins → value = 100 - (7-5)*6.5 = 87.0
    assert result.outputs["value"] == pytest.approx(87.0)


def test_session_override_takes_precedence_over_scenario(
    service: ModelService,
) -> None:
    """Test session override takes precedence over scenario."""
    service.override_input("rates", "rate", 5.5)
    result = service.run_scenario("stress")
    # session override rate=5.5 wins over scenario's rate=6.0
    # value = 100 - (5.5-5)*6.5 = 96.75
    assert result.outputs["value"] == pytest.approx(96.75)


def test_reset_overrides_clears_all(service: ModelService) -> None:
    """Test reset overrides clears all."""
    service.override_input("rates", "rate", 6.0)
    service.reset_overrides()
    result = service.run_scenario("base")
    assert result.outputs["value"] == pytest.approx(100.0)


def test_reset_overrides_returns_count_message(service: ModelService) -> None:
    """Test reset overrides returns count message."""
    service.override_input("rates", "rate", 6.0)
    msg = service.reset_overrides()
    assert "1" in msg


def test_override_same_field_replaces(service: ModelService) -> None:
    """Test override same field replaces."""
    service.override_input("rates", "rate", 6.0)
    service.override_input("rates", "rate", 7.0)
    assert len(service.get_active_overrides()) == 1
    assert service.get_active_overrides()[0].value == 7.0


def test_compare_scenarios_returns_differences(service: ModelService) -> None:
    """Test compare scenarios returns differences."""
    comparison = service.compare_scenarios("base", "stress")
    assert "value" in comparison.differences
    diff = comparison.differences["value"]
    assert diff["a"] == pytest.approx(100.0)
    assert diff["b"] == pytest.approx(93.5)
    assert diff["delta"] == pytest.approx(-6.5)
    assert diff["pct_change"] == pytest.approx(-6.5)


def test_compare_scenarios_with_metrics_filter(service: ModelService) -> None:
    """Test compare scenarios with metrics filter."""
    comparison = service.compare_scenarios("base", "stress", metrics=["value"])
    assert comparison.metrics == ["value"]


def test_get_current_results_empty_at_start(service: ModelService) -> None:
    """Test get current results empty at start."""
    assert service.get_current_results() == {}


def test_get_current_results_after_run(service: ModelService) -> None:
    """Test get current results after run."""
    service.run_scenario("base")
    results = service.get_current_results()
    assert "base" in results


def test_get_model_schema(service: ModelService) -> None:
    """Test get model schema."""
    schema = service.get_model_schema()
    assert schema.name == "Test Model"
    assert len(schema.inputs) == 1
