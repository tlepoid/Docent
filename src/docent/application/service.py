"""Application service layer — the single entry point for all business logic.

All adapters (CLI, MCP server, AI orchestrator) call into this service.
No business logic lives in adapters. No framework code lives here.
"""

from __future__ import annotations

from typing import Any

from docent.domain.models import (
    ModelSchema,
    Override,
    ScenarioComparison,
    ScenarioDefinition,
    ScenarioResult,
)
from docent.domain.ports import ModelRepository, ScenarioRunner


class ModelService:
    """
    Framework-agnostic application service layer.

    Owns session state (active overrides, cached results). Delegates
    scenario execution to the ScenarioRunner port and model metadata
    to the ModelRepository port.
    """

    def __init__(self, runner: ScenarioRunner, repository: ModelRepository) -> None:
        """Initialise the service with a runner and repository."""
        self._runner = runner
        self._repository = repository
        self._overrides: list[Override] = []
        self._last_results: dict[str, ScenarioResult] = {}

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_available_scenarios(self) -> list[ScenarioDefinition]:
        """Return all configured scenarios with their descriptions."""
        return self._repository.get_scenarios()

    def get_current_results(self) -> dict[str, ScenarioResult]:
        """Return the most recent result for each scenario run this session."""
        return dict(self._last_results)

    def get_model_schema(self) -> ModelSchema:
        """Return the full structured description of model inputs and outputs."""
        return self._repository.get_schema()

    def get_active_overrides(self) -> list[Override]:
        """Return all currently active session-level input overrides."""
        return list(self._overrides)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def run_scenario(
        self,
        name: str,
        overrides: dict[str, Any] | None = None,
    ) -> ScenarioResult:
        """
        Run a named scenario, merging active overrides with any call-specific overrides.

        Precedence (highest wins): call-specific overrides > session overrides >
        scenario definition overrides > model base inputs.
        """
        scenarios = {s.name: s for s in self._repository.get_scenarios()}
        if name not in scenarios:
            available = ", ".join(scenarios.keys())
            raise ValueError(f"Unknown scenario '{name}'. Available: {available}")

        scenario = scenarios[name]

        combined: dict[str, Any] = {}
        for ov in self._overrides:
            combined[ov.field] = ov.value
        if overrides:
            combined.update(overrides)

        result = self._runner.run(scenario, extra_overrides=combined)
        self._last_results[name] = result
        return result

    def override_input(self, source: str, field: str, value: float) -> str:
        """Apply a session-level override to a specific input field.

        Replaces any existing override for the same field.
        """
        self._overrides = [o for o in self._overrides if o.field != field]
        self._overrides.append(Override(source=source, field=field, value=value))
        return f"Override applied: {source}.{field} = {value}"

    def reset_overrides(self) -> str:
        """Clear all active session-level input overrides."""
        count = len(self._overrides)
        self._overrides = []
        return f"Cleared {count} override(s). All inputs restored to model defaults."

    def compare_scenarios(
        self,
        scenario_a: str,
        scenario_b: str,
        metrics: list[str] | None = None,
    ) -> ScenarioComparison:
        """Run two scenarios and return a structured side-by-side comparison.

        If metrics is None, all output fields present in both results are compared.
        """
        result_a = self.run_scenario(scenario_a)
        result_b = self.run_scenario(scenario_b)

        all_outputs = set(result_a.outputs.keys()) | set(result_b.outputs.keys())
        compare_metrics = metrics if metrics else sorted(all_outputs)

        differences: dict[str, dict] = {}
        for metric in compare_metrics:
            val_a = result_a.outputs.get(metric)
            val_b = result_b.outputs.get(metric)
            if val_a is not None and val_b is not None:
                try:
                    delta = float(val_b) - float(val_a)
                    pct = (delta / float(val_a) * 100) if val_a != 0 else None
                    differences[metric] = {
                        "a": val_a,
                        "b": val_b,
                        "delta": round(delta, 6),
                        "pct_change": round(pct, 2) if pct is not None else None,
                    }
                except (TypeError, ValueError):
                    differences[metric] = {
                        "a": val_a,
                        "b": val_b,
                        "delta": None,
                        "pct_change": None,
                    }
            else:
                differences[metric] = {
                    "a": val_a,
                    "b": val_b,
                    "delta": None,
                    "pct_change": None,
                }

        return ScenarioComparison(
            scenario_a=result_a,
            scenario_b=result_b,
            metrics=compare_metrics,
            differences=differences,
        )
