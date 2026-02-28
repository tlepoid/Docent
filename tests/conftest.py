"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from docent.adapters.data.in_memory import (
    FunctionalScenarioRunner,
    InMemoryModelRepository,
)
from docent.application.service import PortfolioService
from docent.domain.models import (
    InputField,
    ModelSchema,
    OutputField,
    ScenarioDefinition,
)


@pytest.fixture
def schema() -> ModelSchema:
    """Build a minimal test ModelSchema."""
    return ModelSchema(
        name="Test Model",
        description="A minimal test model.",
        inputs=[
            InputField(
                name="rate",
                source="rates",
                description="Interest rate",
                units="%",
                typical_min=0.0,
                typical_max=10.0,
                current_value=5.0,
            )
        ],
        outputs=[
            OutputField(
                name="value",
                description="Portfolio value",
                units="£m",
                interpretation="Higher is better.",
            )
        ],
        assumptions=["Rate is flat."],
        caveats=["Demo only."],
    )


@pytest.fixture
def scenarios() -> list[ScenarioDefinition]:
    """Build a minimal list of test ScenarioDefinitions."""
    return [
        ScenarioDefinition(
            name="base",
            description="Base case",
            stress_rationale="Baseline",
            overrides={},
        ),
        ScenarioDefinition(
            name="stress",
            description="Rate shock +100bp",
            stress_rationale="100bp rate rise",
            overrides={"rate": 6.0},
        ),
    ]


@pytest.fixture
def simple_model() -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a trivial model function: value = 100 - (rate - 5) * 6.5."""

    def model(inputs: dict) -> dict:
        rate = inputs.get("rate", 5.0)
        return {"value": round(100.0 - (rate - 5.0) * 6.5, 4)}

    return model


@pytest.fixture
def service(
    schema: ModelSchema,
    scenarios: list[ScenarioDefinition],
    simple_model: Callable[[dict[str, Any]], dict[str, Any]],
) -> PortfolioService:
    """Build a wired PortfolioService backed by the test schema and scenarios."""
    repository = InMemoryModelRepository(schema=schema, scenarios=scenarios)
    runner = FunctionalScenarioRunner(
        model_fn=simple_model,
        base_inputs={"rate": 5.0},
    )
    return PortfolioService(runner=runner, repository=repository)
