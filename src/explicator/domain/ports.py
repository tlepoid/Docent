"""Abstract ports — interfaces that adapters must implement.

These define the boundary between the application layer and the
infrastructure/data layer. Concrete implementations live in adapters/data/.
"""

from abc import ABC, abstractmethod
from typing import Any

from explicator.domain.models import (
    InputField,
    ModelSchema,
    ScenarioDefinition,
    ScenarioResult,
)


class ScenarioRunner(ABC):
    """Port: executes scenarios against the underlying model."""

    @abstractmethod
    def run(
        self,
        scenario: ScenarioDefinition,
        extra_overrides: dict[str, Any],
    ) -> ScenarioResult:
        """Run a scenario with optional additional overrides beyond the definition."""


class ModelRepository(ABC):
    """Port: provides access to model configuration and metadata."""

    @abstractmethod
    def get_scenarios(self) -> list[ScenarioDefinition]:
        """Return all available scenario definitions."""

    @abstractmethod
    def get_schema(self) -> ModelSchema:
        """Return the full model schema."""

    @abstractmethod
    def get_inputs(self) -> list[InputField]:
        """Return current state of all model inputs."""
