"""MCP Server adapter for Docent.

Exposes the ModelService as an MCP server with tools, resources, and prompts.
This adapter sits alongside the CLI as a parallel entry point into the application
layer — it does not bypass or duplicate any domain logic.

Start with:
    python -m docent.adapters.mcp_server
or via the entry point:
    docent-mcp
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from docent.application.service import ModelService

# Module-level service instance set by the application wiring.
# Using a module-level variable allows the MCP decorators to close over it
# while keeping the server testable via set_service().
_service: ModelService | None = None

mcp = FastMCP("Docent")


def set_service(service: ModelService) -> None:
    """Wire the ModelService instance used by this MCP server."""
    global _service
    _service = service


def _get_service() -> ModelService:
    if _service is None:
        raise RuntimeError(
            "ModelService has not been wired. "
            "Call set_service() before starting the server."
        )
    return _service


# ------------------------------------------------------------------
# Tools — actions Claude can invoke
# ------------------------------------------------------------------


@mcp.tool()
def run_scenario(name: str, overrides: dict[str, float] | None = None) -> dict:
    """
    Run a named scenario through the portfolio model.

    Applies any active session-level overrides plus any overrides provided here
    (call-specific overrides take precedence). Returns the full set of model outputs.
    """
    try:
        result = _get_service().run_scenario(name, overrides=overrides)
        return result.to_dict()
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def override_input(source: str, field: str, value: float) -> dict:
    """
    Apply a persistent session-level override to a model input.

    This override is applied to all subsequent scenario runs until
    reset_overrides is called. Use source to group related inputs
    (e.g. "rates", "credit", "equity").
    """
    try:
        message = _get_service().override_input(source, field, value)
        return {"message": message, "source": source, "field": field, "value": value}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def reset_overrides() -> dict:
    """Clear all active session-level overrides, restoring model defaults."""
    try:
        message = _get_service().reset_overrides()
        return {"message": message}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def compare_scenarios(
    scenario_a: str,
    scenario_b: str,
    metrics: list[str] | None = None,
) -> dict:
    """
    Run two scenarios and return a structured side-by-side comparison.

    Returns absolute deltas and percentage changes for each output metric.
    If metrics is not provided, all shared output fields are compared.
    """
    try:
        comparison = _get_service().compare_scenarios(scenario_a, scenario_b, metrics)
        return comparison.to_dict()
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def get_available_scenarios() -> dict:
    """List all configured scenarios with names, descriptions, and stress rationale."""
    try:
        scenarios = _get_service().get_available_scenarios()
        return {"scenarios": [s.to_dict() for s in scenarios]}
    except Exception as exc:
        return {"error": str(exc)}


# ------------------------------------------------------------------
# Resources — context Claude can read
# ------------------------------------------------------------------


@mcp.resource("model://schema")
def get_model_schema() -> str:
    """
    Full structured description of all model inputs, outputs, assumptions, and caveats.

    This is the primary source of truth for Claude's understanding of the domain.
    Includes financial meaning, units, typical ranges, and interpretation guidance
    for every field.
    """
    try:
        schema = _get_service().get_model_schema()
        return json.dumps(schema.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.resource("model://scenarios")
def get_scenarios_resource() -> str:
    """Return scenario definitions, including what each is designed to stress-test."""
    try:
        scenarios = _get_service().get_available_scenarios()
        return json.dumps([s.to_dict() for s in scenarios], indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.resource("model://results/latest")
def get_latest_results() -> str:
    """Most recent run results for all scenarios executed this session."""
    try:
        results = _get_service().get_current_results()
        return json.dumps(
            {name: r.to_dict() for name, r in results.items()},
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.resource("model://overrides/current")
def get_current_overrides() -> str:
    """All input overrides currently active in this session."""
    try:
        overrides = _get_service().get_active_overrides()
        return json.dumps([o.to_dict() for o in overrides], indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ------------------------------------------------------------------
# Prompts — reusable AI prompt templates
# ------------------------------------------------------------------


@mcp.prompt()
def explain_scenario_result(scenario_name: str) -> str:
    """Explain what drove the result of a given scenario in plain English."""
    try:
        results = _get_service().get_current_results()
        schema = _get_service().get_model_schema()

        if scenario_name not in results:
            return (
                f"No result found for scenario '{scenario_name}'. "
                f"Run it first using the run_scenario tool."
            )

        result = results[scenario_name]
        return (
            f"You are a portfolio risk analyst. Explain the following scenario result "
            f"in plain English to a non-technical stakeholder.\n\n"
            f"Model: {schema.name}\n"
            f"Scenario: {scenario_name}\n\n"
            f"Inputs used:\n{json.dumps(result.inputs_used, indent=2)}\n\n"
            f"Overrides applied:\n{json.dumps(result.overrides_applied, indent=2)}\n\n"
            f"Outputs:\n{json.dumps(result.outputs, indent=2)}\n\n"
            f"Focus on: what drove the key outputs, what risks this scenario reveals, "
            f"and what a portfolio manager should take away from this result."
        )
    except Exception as exc:
        return f"Error generating prompt: {exc}"


@mcp.prompt()
def compare_scenarios_narrative(scenario_a: str, scenario_b: str) -> str:
    """Narrate the key differences between two scenario outcomes in plain English."""
    try:
        schema = _get_service().get_model_schema()
        comparison = _get_service().compare_scenarios(scenario_a, scenario_b)
        return (
            f"You are a portfolio risk analyst. Compare these two scenario outcomes "
            f"and narrate the key differences for a senior investment committee.\n\n"
            f"Model: {schema.name}\n"
            f"Comparing: '{scenario_a}' vs '{scenario_b}'\n\n"
            "Comparison data:\n"
            f"{json.dumps(comparison.to_dict(), indent=2)}\n\n"
            "Focus on: the most significant differences, which scenario is more "
            "stressful and why, and what risk factors are driving the divergence."
        )
    except Exception as exc:
        return f"Error generating prompt: {exc}"


@mcp.prompt()
def summarise_portfolio_risk() -> str:
    """Summarise current risk exposures across all scenarios that have been run."""
    try:
        results = _get_service().get_current_results()
        schema = _get_service().get_model_schema()
        overrides = _get_service().get_active_overrides()

        if not results:
            return (
                "No scenarios have been run yet. Use the run_scenario tool to execute "
                "one or more scenarios before requesting a risk summary."
            )

        return (
            f"You are a chief risk officer. Summarise the portfolio's current risk "
            f"exposures based on the scenario results below.\n\n"
            f"Model: {schema.name}\n"
            "Active overrides: "
            f"{json.dumps([o.to_dict() for o in overrides], indent=2)}\n\n"
            "Scenario results:\n"
            f"{json.dumps({n: r.to_dict() for n, r in results.items()}, indent=2)}\n\n"
            "Focus on: overall risk level, which scenarios are most severe, "
            "key drivers of risk, and any concentrations or tail risks to flag."
        )
    except Exception as exc:
        return f"Error generating prompt: {exc}"


@mcp.prompt()
def explain_input_sensitivity(input_field: str) -> str:
    """Explain how sensitive the model is to a given input field."""
    try:
        schema = _get_service().get_model_schema()
        field_info = next((i for i in schema.inputs if i.name == input_field), None)
        field_desc = (
            json.dumps(field_info.to_dict(), indent=2)
            if field_info
            else f"Field '{input_field}' not found in schema."
        )
        return (
            "You are a quantitative analyst. Explain how sensitive this portfolio "
            "model is to the following input, and what happens when it moves.\n\n"
            f"Model: {schema.name}\n"
            f"Input field: {input_field}\n"
            f"Field details:\n{field_desc}\n\n"
            "Explain: the financial meaning of this input, what drives it in practice, "
            f"how the portfolio is exposed to it, and what a 1 standard deviation move "
            f"might mean for portfolio outcomes."
        )
    except Exception as exc:
        return f"Error generating prompt: {exc}"


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def main() -> None:
    """Start the MCP server.

    Reads an optional service path from the first CLI argument::

        docent-mcp myapp.model:build_service

    Falls back to stub wiring if no path is given.
    """
    import sys

    if len(sys.argv) > 1:
        import docent as _docent

        service = _docent.load_service(sys.argv[1])
    else:
        from docent.adapters.data.in_memory import _build_stub_wiring

        repository, runner = _build_stub_wiring()
        service = ModelService(runner=runner, repository=repository)

    set_service(service)
    mcp.run()
