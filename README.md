<div align="center">
  <img src="docs/docent-icon.svg" width="80" height="80" />

# Docent

</div>

`Docent` guides users through your data application the way a museum docent guides visitors through an exhibition — bringing expert context to complex material. It adds a natural language AI interface to scenario-driven modelling applications, letting non-technical users ask questions, run scenarios, and interpret results without leaving their workflow.

Provider-agnostic by design, Docent works with Claude, Azure OpenAI, Copilot, or any LLM your organisation uses.

---

## Project Structure

```
docent/
├── src/docent/
│   ├── domain/              # Core data structures and abstract ports
│   │   ├── models.py        # ScenarioDefinition, ScenarioResult, ModelSchema, etc.
│   │   └── ports.py         # ScenarioRunner, ModelRepository (abstract interfaces)
│   ├── application/
│   │   └── service.py       # ModelService — single entry point for all business logic
│   ├── adapters/
│   │   ├── cli/             # Click-based CLI adapter
│   │   ├── mcp_server/      # FastMCP server adapter (for Claude Desktop / MCP clients)
│   │   └── data/            # Infrastructure adapters (in-memory implementations)
│   ├── ai/
│   │   ├── tools/           # Tool definitions in OpenAI function-calling JSON schema format
│   │   ├── providers/       # Provider adapters: Claude, Azure OpenAI (+ abstract base)
│   │   └── dispatcher.py    # Shared tool dispatcher (provider-agnostic)
│   └── config.py            # Configuration via environment variables
├── examples/
│   └── demo_model/          # Bond portfolio risk model — shows how to wire Docent
├── docs/
│   └── model_schema.md      # Rich domain description for AI context
└── tests/
    ├── unit/
    └── integration/
```

`docent` is the library — install it as a dependency and build your model on top of it, just as you would with `fastapi` or `click`. Your model code lives in your own project; `docent` provides the service layer, AI interface, CLI, and MCP server.

---

## Quick Start

### 1. Install

```bash
pip install -e ".[claude,dev]"
```

For Azure OpenAI instead:

```bash
pip install -e ".[azure,dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your API key and provider
```

### 3. Run the demo CLI

```bash
# List scenarios
docent --service examples.demo_model.model:build_service scenarios

# Run a scenario
docent --service examples.demo_model.model:build_service run base_case

# Run with an override
docent --service examples.demo_model.model:build_service run base_case -o credit_spread_ig=2.5

# Compare two scenarios
docent --service examples.demo_model.model:build_service compare base_case credit_stress

# Chat with an AI about the model
docent --service examples.demo_model.model:build_service chat
```

Set `DOCENT_SERVICE` in your environment to avoid repeating the flag:

```bash
export DOCENT_SERVICE=examples.demo_model.model:build_service
docent run base_case
docent chat "what happens to duration in the stagflation scenario?"
```

### 4. Start the MCP Server

**With the demo model:**

```bash
uv run mcp dev examples/demo_model/run_mcp.py
```

**Via the entry point:**

```bash
docent-mcp examples.demo_model.model:build_service
# or
python -m docent.adapters.mcp_server examples.demo_model.model:build_service
```

### 5. Connect Claude Desktop

Copy `claude_desktop_config.json.example` into your Claude Desktop config:

```json
{
  "mcpServers": {
    "docent": {
      "command": "python",
      "args": ["-m", "docent.adapters.mcp_server", "myapp.model:build_service"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Then ask Claude things like:

- _"Run the credit stress scenario and tell me what happened to portfolio duration."_
- _"Override the credit spread input to 250bps and rerun the base case."_
- _"What are the key assumptions in this model?"_
- _"Compare the stagflation and rates_shock_up scenarios."_

---

## Connecting Your Own Model

`docent` is a library — your model code lives in your own project. A typical layout:

```
my-risk-app/
├── pyproject.toml           # dependencies = ["docent[claude]"]
├── .env                     # ANTHROPIC_API_KEY=...
└── src/myapp/
    ├── model.py             # schema, scenarios, model_fn, build_service()
    └── run_mcp.py           # calls docent.run_mcp(service)
```

```python
# src/myapp/model.py
import docent

service = docent.create(
    model_fn=my_model_fn,
    base_inputs=MY_BASE_INPUTS,
    schema=MY_SCHEMA,
    scenarios=MY_SCENARIOS,
)
```

```python
# src/myapp/run_mcp.py
import docent
from myapp.model import service

if __name__ == "__main__":
    docent.run_mcp(service)
```

```bash
# CLI — point --service at any module:attribute that returns a ModelService
docent --service myapp.model:service scenarios
docent --service myapp.model:service run base_case
docent --service myapp.model:service chat
```

Docent uses the ports & adapters pattern. The quickest way to wire up any Python model function:

```python
import docent

def my_model(inputs: dict) -> dict:
    # Your model logic here
    return {"metric_a": ..., "metric_b": ...}

service = docent.create(
    model_fn=my_model,
    base_inputs=MY_BASE_INPUTS,
    schema=MY_SCHEMA,
    scenarios=MY_SCENARIOS,
)

if __name__ == "__main__":
    docent.run_mcp(service)
```

For custom storage or execution backends, implement `ScenarioRunner` and `ModelRepository` directly and pass them to `ModelService`:

```python
from docent import ModelService
from docent.domain.ports import ScenarioRunner, ModelRepository

class MyRunner(ScenarioRunner): ...
class MyRepository(ModelRepository): ...

service = ModelService(runner=MyRunner(), repository=MyRepository())
```

See `examples/demo_model/model.py` for a complete worked example.

---

## AI Provider Configuration

Set `AI_PROVIDER` in your environment:

| Value              | Provider         | Required env vars                                                          |
| ------------------ | ---------------- | -------------------------------------------------------------------------- |
| `claude` (default) | Anthropic Claude | `ANTHROPIC_API_KEY`                                                        |
| `azure_openai`     | Azure OpenAI     | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |

Tool definitions live in `src/docent/ai/tools/definitions.py` in OpenAI function-calling
JSON schema format — a single source of truth consumed by all providers.

---

## Running Tests

```bash
pytest
```

---

## Architecture

Docent enforces strict separation between layers:

- **Domain** (`domain/`) — pure Python dataclasses and abstract interfaces; no framework code
- **Application** (`application/service.py`) — business logic; no framework code; tested directly
- **Adapters** (`adapters/`) — thin translation layers; CLI and MCP server both call `ModelService`
- **AI** (`ai/`) — provider adapters and dispatcher; no business logic; no provider-specific code outside its own module

The MCP server and CLI are parallel entry points into the same application layer. They share no code with each other except through `ModelService`.
