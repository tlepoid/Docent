"""In-memory implementations of the domain ports.

Useful for testing and for wiring up demo/example models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from ...domain.models import (
    InputField,
    ModelSchema,
    OutputField,
    ScenarioDefinition,
    ScenarioResult,
)
from ...domain.ports import ModelRepository, ScenarioRunner


class InMemoryModelRepository(ModelRepository):
    """
    A fully in-memory ModelRepository.

    Construct with a ModelSchema and list of ScenarioDefinitions.
    Suitable for testing and for wrapping functional demo models.
    """

    def __init__(self, schema: ModelSchema, scenarios: list[ScenarioDefinition]) -> None:
        self._schema = schema
        self._scenarios = scenarios

    def get_scenarios(self) -> list[ScenarioDefinition]:
        return list(self._scenarios)

    def get_schema(self) -> ModelSchema:
        return self._schema

    def get_inputs(self) -> list[InputField]:
        return list(self._schema.inputs)


class FunctionalScenarioRunner(ScenarioRunner):
    """
    A ScenarioRunner that delegates to a user-supplied callable.

    The callable receives the merged inputs dict and returns an outputs dict.
    This lets you wrap any pure Python model function without subclassing.

    Example::

        runner = FunctionalScenarioRunner(
            model_fn=my_model,
            base_inputs={"rate": 5.0, "spread": 1.2},
        )
    """

    def __init__(
        self,
        model_fn: Callable[[dict[str, Any]], dict[str, Any]],
        base_inputs: dict[str, Any],
    ) -> None:
        self._model_fn = model_fn
        self._base_inputs = base_inputs

    def run(
        self,
        scenario: ScenarioDefinition,
        extra_overrides: dict[str, Any],
    ) -> ScenarioResult:
        inputs = dict(self._base_inputs)
        inputs.update(scenario.overrides)
        inputs.update(extra_overrides)

        outputs = self._model_fn(inputs)

        return ScenarioResult(
            scenario_name=scenario.name,
            inputs_used=inputs,
            outputs=outputs,
            overrides_applied={**scenario.overrides, **extra_overrides},
            run_at=datetime.now(timezone.utc).isoformat(),
        )


def _build_stub_wiring() -> tuple[InMemoryModelRepository, FunctionalScenarioRunner]:
    """
    Fallback stub wiring used when no real model is configured.
    Returns a minimal repository and runner so the server starts without error.
    Replace this in your own entry point with real implementations.
    """
    schema = ModelSchema(
        name="Stub Model",
        description=(
            "No model has been configured. "
            "Wire a real ModelRepository and ScenarioRunner in your entry point."
        ),
        inputs=[],
        outputs=[
            OutputField(
                name="stub",
                description="Placeholder output.",
                units="",
                interpretation="Replace this model with a real implementation.",
            )
        ],
        assumptions=["This is a stub."],
        caveats=["Wire a real model before use."],
    )
    scenarios = [
        ScenarioDefinition(
            name="base",
            description="Stub base case.",
            stress_rationale="Stub — no real stress applied.",
            overrides={},
        )
    ]
    repo = InMemoryModelRepository(schema=schema, scenarios=scenarios)
    runner = FunctionalScenarioRunner(
        model_fn=lambda inputs: {"stub": True, "message": "No model configured."},
        base_inputs={},
    )
    return repo, runner
