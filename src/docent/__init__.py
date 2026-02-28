"""Docent — provider-agnostic AI interface for scenario-driven modelling."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from docent.adapters.data.in_memory import (
    FunctionalScenarioRunner,
    InMemoryModelRepository,
)
from docent.application.service import ModelService
from docent.domain.models import (
    InputField,
    ModelSchema,
    OutputField,
    Override,
    ScenarioComparison,
    ScenarioDefinition,
    ScenarioResult,
)
from docent.domain.ports import ModelRepository, ScenarioRunner

if TYPE_CHECKING:
    from docent.ai.providers.base import AIProvider

__version__ = "0.1.0"

__all__ = [
    "ModelService",
    "ModelSchema",
    "InputField",
    "OutputField",
    "ScenarioDefinition",
    "ScenarioResult",
    "ScenarioComparison",
    "Override",
    "FunctionalScenarioRunner",
    "InMemoryModelRepository",
    "ModelRepository",
    "ScenarioRunner",
    "create",
    "run_mcp",
    "run_chat",
    "load_service",
]


def create(
    model_fn: Callable[[dict[str, Any]], dict[str, Any]],
    base_inputs: dict[str, Any],
    schema: ModelSchema,
    scenarios: list[ScenarioDefinition],
) -> ModelService:
    """Create a ModelService from a model function, schema, and scenario list.

    This is the quickest way to wrap a plain Python model function.
    For custom storage or execution backends, instantiate ModelService directly
    using your own ModelRepository and ScenarioRunner implementations.

    Example::

        service = docent.create(
            model_fn=my_model,
            base_inputs={"rate": 5.0},
            schema=my_schema,
            scenarios=my_scenarios,
        )
    """
    repo = InMemoryModelRepository(schema=schema, scenarios=scenarios)
    runner = FunctionalScenarioRunner(model_fn=model_fn, base_inputs=base_inputs)
    return ModelService(runner=runner, repository=repo)


def run_mcp(service: ModelService) -> None:
    """Start the MCP server backed by the given service.

    Intended as the entry point in your run script::

        if __name__ == "__main__":
            docent.run_mcp(service)
    """
    from docent.adapters.mcp_server.server import mcp, set_service

    set_service(service)
    mcp.run()


def run_chat(
    service: ModelService,
    *,
    question: str | None = None,
) -> None:
    """Start an interactive chat REPL, or answer a single question.

    Requires an AI provider to be configured (e.g. ANTHROPIC_API_KEY).

    Args:
        service: The ModelService to query.
        question: If provided, answer this single question and return.
                  If omitted, start an interactive REPL.
    """
    from docent.ai.dispatcher import ToolDispatcher
    from docent.ai.providers.base import AIMessage
    from docent.ai.tools.definitions import TOOL_DEFINITIONS
    from docent.config import build_provider

    provider = build_provider()
    dispatcher = ToolDispatcher(service)

    def _turn(messages: list[AIMessage]) -> str:
        while True:
            response = provider.chat(messages, tools=TOOL_DEFINITIONS)
            messages.append(response.message)
            if not response.tool_calls:
                return response.message.content or ""
            for tc in response.tool_calls:
                result = dispatcher.dispatch(tc["name"], tc["arguments"])
                messages.append(
                    AIMessage(
                        role="tool",
                        content=json.dumps(result),
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    )
                )

    if question:
        print(_turn([AIMessage(role="user", content=question)]))
        return

    print("Docent chat — type 'exit' or Ctrl+D to quit.\n")
    messages: list[AIMessage] = []
    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        messages.append(AIMessage(role="user", content=user_input))
        print(f"\n{_turn(messages)}\n")


def load_service(path: str) -> ModelService:
    """Load a ModelService from a dotted import path.

    The path format is ``'module.path:attribute'``, where the attribute is
    either a ``ModelService`` instance or a zero-argument callable that returns
    one.

    Example::

        service = docent.load_service("myapp.model:build_service")
        service = docent.load_service("myapp.model:service")
    """
    import importlib

    if ":" not in path:
        raise ValueError(
            f"Service path must be 'module:attribute', got '{path}'. "
            "Example: 'myapp.model:build_service'"
        )
    module_path, attr = path.rsplit(":", 1)
    module = importlib.import_module(module_path)
    obj = getattr(module, attr)
    return obj() if callable(obj) else obj
