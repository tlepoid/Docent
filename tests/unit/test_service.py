"""Unit tests for PortfolioService."""

import pytest

from docent.application.service import PortfolioService


def test_get_available_scenarios(service: PortfolioService) -> None:
    scenarios = service.get_available_scenarios()
    assert len(scenarios) == 2
    names = {s.name for s in scenarios}
    assert names == {"base", "stress"}


def test_run_scenario_base(service: PortfolioService) -> None:
    result = service.run_scenario("base")
    assert result.scenario_name == "base"
    assert result.outputs["value"] == pytest.approx(100.0)


def test_run_scenario_stress(service: PortfolioService) -> None:
    result = service.run_scenario("stress")
    # stress overrides rate=6.0 → value = 100 - (6-5)*6.5 = 93.5
    assert result.outputs["value"] == pytest.approx(93.5)


def test_run_scenario_unknown_raises(service: PortfolioService) -> None:
    with pytest.raises(ValueError, match="Unknown scenario"):
        service.run_scenario("nonexistent")


def test_override_input_persists(service: PortfolioService) -> None:
    service.override_input("rates", "rate", 6.0)
    result = service.run_scenario("base")
    assert result.outputs["value"] == pytest.approx(93.5)


def test_call_override_takes_precedence_over_session(service: PortfolioService) -> None:
    service.override_input("rates", "rate", 6.0)
    result = service.run_scenario("base", overrides={"rate": 7.0})
    # rate=7.0 wins → value = 100 - (7-5)*6.5 = 87.0
    assert result.outputs["value"] == pytest.approx(87.0)


def test_session_override_takes_precedence_over_scenario(service: PortfolioService) -> None:
    service.override_input("rates", "rate", 5.5)
    result = service.run_scenario("stress")
    # session override rate=5.5 wins over scenario's rate=6.0
    # value = 100 - (5.5-5)*6.5 = 96.75
    assert result.outputs["value"] == pytest.approx(96.75)


def test_reset_overrides_clears_all(service: PortfolioService) -> None:
    service.override_input("rates", "rate", 6.0)
    service.reset_overrides()
    result = service.run_scenario("base")
    assert result.outputs["value"] == pytest.approx(100.0)


def test_reset_overrides_returns_count_message(service: PortfolioService) -> None:
    service.override_input("rates", "rate", 6.0)
    msg = service.reset_overrides()
    assert "1" in msg


def test_override_same_field_replaces(service: PortfolioService) -> None:
    service.override_input("rates", "rate", 6.0)
    service.override_input("rates", "rate", 7.0)
    assert len(service.get_active_overrides()) == 1
    assert service.get_active_overrides()[0].value == 7.0


def test_compare_scenarios_returns_differences(service: PortfolioService) -> None:
    comparison = service.compare_scenarios("base", "stress")
    assert "value" in comparison.differences
    diff = comparison.differences["value"]
    assert diff["a"] == pytest.approx(100.0)
    assert diff["b"] == pytest.approx(93.5)
    assert diff["delta"] == pytest.approx(-6.5)
    assert diff["pct_change"] == pytest.approx(-6.5)


def test_compare_scenarios_with_metrics_filter(service: PortfolioService) -> None:
    comparison = service.compare_scenarios("base", "stress", metrics=["value"])
    assert comparison.metrics == ["value"]


def test_get_current_results_empty_at_start(service: PortfolioService) -> None:
    assert service.get_current_results() == {}


def test_get_current_results_after_run(service: PortfolioService) -> None:
    service.run_scenario("base")
    results = service.get_current_results()
    assert "base" in results


def test_get_model_schema(service: PortfolioService) -> None:
    schema = service.get_model_schema()
    assert schema.name == "Test Model"
    assert len(schema.inputs) == 1
