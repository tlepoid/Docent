"""Tool execution dispatcher — shared across all AI providers.

When any provider returns a tool call, this dispatcher handles it by routing
to the appropriate PortfolioService method. Provider identity is irrelevant here:
the same dispatcher handles tool calls from Claude, Azure OpenAI, or any other provider.
"""

from __future__ import annotations

from typing import Any

from docent.application.service import PortfolioService


class ToolDispatcher:
    """
    Routes tool call requests from AI providers to the PortfolioService.

    Always returns a JSON-serialisable dict. Errors are returned as structured
    dicts rather than raised, so the provider can relay them to the user.
    """

    def __init__(self, service: PortfolioService) -> None:
        """Initialise with the PortfolioService to dispatch tool calls to."""
        self._service = service
        self._handlers: dict[str, Any] = {
            "run_scenario": self._run_scenario,
            "override_input": self._override_input,
            "reset_overrides": self._reset_overrides,
            "compare_scenarios": self._compare_scenarios,
            "get_available_scenarios": self._get_available_scenarios,
        }

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a named tool with the given arguments.

        Returns a JSON-serialisable dict. Never raises.
        """
        try:
            handler = self._handlers.get(name)
            if handler is None:
                return {"error": f"Unknown tool '{name}'."}
            return handler(**arguments)
        except Exception as exc:
            return {"error": str(exc)}

    def _run_scenario(self, name: str, overrides: dict | None = None) -> dict:
        result = self._service.run_scenario(name, overrides=overrides)
        return result.to_dict()

    def _override_input(self, source: str, field: str, value: float) -> dict:
        message = self._service.override_input(source, field, value)
        return {"message": message, "source": source, "field": field, "value": value}

    def _reset_overrides(self) -> dict:
        message = self._service.reset_overrides()
        return {"message": message}

    def _compare_scenarios(
        self,
        scenario_a: str,
        scenario_b: str,
        metrics: list[str] | None = None,
    ) -> dict:
        comparison = self._service.compare_scenarios(scenario_a, scenario_b, metrics)
        return comparison.to_dict()

    def _get_available_scenarios(self) -> dict:
        scenarios = self._service.get_available_scenarios()
        return {"scenarios": [s.to_dict() for s in scenarios]}
