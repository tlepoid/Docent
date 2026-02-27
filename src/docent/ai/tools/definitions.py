"""Tool definitions in OpenAI function-calling JSON schema format.

This module is the single source of truth for all tool schemas.
All AI providers (Claude, Azure OpenAI, etc.) consume these definitions
and translate to their own wire format internally.

No provider-specific code lives here.
"""

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "run_scenario",
            "description": (
                "Run a named scenario through the portfolio model, optionally applying "
                "additional input overrides for this run only. Returns the full set of "
                "model outputs including portfolio metrics."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the scenario to run.",
                    },
                    "overrides": {
                        "type": "object",
                        "description": (
                            "Optional map of input field names to numeric values to "
                            "override for this run only. These do not persist between calls."
                        ),
                        "additionalProperties": {"type": "number"},
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "override_input",
            "description": (
                "Apply a persistent session-level override to a specific model input. "
                "This override will be applied to all subsequent scenario runs until "
                "reset_overrides is called."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "The input source group, e.g. 'rates', 'credit', 'equity'.",
                    },
                    "field": {
                        "type": "string",
                        "description": "The field name within that source group.",
                    },
                    "value": {
                        "type": "number",
                        "description": "The numeric value to apply.",
                    },
                },
                "required": ["source", "field", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_overrides",
            "description": (
                "Clear all active session-level input overrides, restoring all model "
                "inputs to their configured defaults."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_scenarios",
            "description": (
                "Run two named scenarios and return a structured side-by-side comparison "
                "of their outputs, including absolute and percentage differences. "
                "Optionally restrict the comparison to specific output metrics."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_a": {
                        "type": "string",
                        "description": "Name of the first scenario.",
                    },
                    "scenario_b": {
                        "type": "string",
                        "description": "Name of the second scenario.",
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of output field names to compare. "
                            "If omitted, all shared outputs are compared."
                        ),
                    },
                },
                "required": ["scenario_a", "scenario_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_scenarios",
            "description": (
                "List all configured scenarios with their names, descriptions, "
                "and stress rationale."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
