"""Core domain model — data structures shared across the entire application.

These are plain dataclasses with no framework dependencies. All adapters
(CLI, MCP server, AI providers) work with these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class InputField:
    """A single model input variable."""

    name: str
    source: str  # logical grouping, e.g. "rates", "credit", "equity"
    description: str
    units: str
    typical_min: float
    typical_max: float
    current_value: float | None = None

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "name": self.name,
            "source": self.source,
            "description": self.description,
            "units": self.units,
            "typical_min": self.typical_min,
            "typical_max": self.typical_max,
            "current_value": self.current_value,
        }


@dataclass
class OutputField:
    """A single model output metric."""

    name: str
    description: str
    units: str
    interpretation: str
    good_threshold: float | None = None  # value below which result is concerning
    bad_threshold: float | None = None  # value below which result is critical

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "name": self.name,
            "description": self.description,
            "units": self.units,
            "interpretation": self.interpretation,
            "good_threshold": self.good_threshold,
            "bad_threshold": self.bad_threshold,
        }


@dataclass
class ModelSchema:
    """Full description of the model's inputs, outputs, assumptions, and caveats."""

    name: str
    description: str
    inputs: list[InputField]
    outputs: list[OutputField]
    assumptions: list[str]
    caveats: list[str]

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "name": self.name,
            "description": self.description,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "assumptions": self.assumptions,
            "caveats": self.caveats,
        }


@dataclass
class ScenarioDefinition:
    """A named scenario with its baseline overrides and stress description."""

    name: str
    description: str
    stress_rationale: str
    overrides: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "name": self.name,
            "description": self.description,
            "stress_rationale": self.stress_rationale,
            "overrides": self.overrides,
        }


@dataclass
class ScenarioResult:
    """The result of running a scenario through the model."""

    scenario_name: str
    inputs_used: dict[str, Any]
    outputs: dict[str, Any]
    overrides_applied: dict[str, Any]
    run_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "scenario_name": self.scenario_name,
            "inputs_used": self.inputs_used,
            "outputs": self.outputs,
            "overrides_applied": self.overrides_applied,
            "run_at": self.run_at,
        }


@dataclass
class Override:
    """A single active session-level input override."""

    source: str
    field: str
    value: Any
    applied_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "source": self.source,
            "field": self.field,
            "value": self.value,
            "applied_at": self.applied_at,
        }


@dataclass
class ScenarioComparison:
    """Side-by-side comparison of two scenario results."""

    scenario_a: ScenarioResult
    scenario_b: ScenarioResult
    metrics: list[str]
    differences: dict[str, dict]  # metric -> {a, b, delta, pct_change}

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "scenario_a": self.scenario_a.to_dict(),
            "scenario_b": self.scenario_b.to_dict(),
            "metrics": self.metrics,
            "differences": self.differences,
        }
