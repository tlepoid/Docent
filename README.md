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
│   │   └── service.py       # PortfolioService — single entry point for all business logic
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
docent scenarios

# Run a scenario
docent run base_case

# Run with an override
docent run base_case -o credit_spread_ig=2.5

# Compare two scenarios
docent compare base_case credit_stress

# Print the model schema
docent schema
```

### 4. Start the MCP Server

**With the demo model:**

```bash
cd examples/demo_model
python run_mcp.py
```

**Default stub (replace with your own model):**

```bash
docent-mcp
# or
python -m docent.adapters.mcp_server
```

### 5. Connect Claude Desktop

Copy `claude_desktop_config.json.example` into your Claude Desktop config:

```json
{
  "mcpServers": {
    "docent": {
      "command": "python",
      "args": ["-m", "docent.adapters.mcp_server"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Then ask Claude things like:
- *"Run the credit stress scenario and tell me what happened to portfolio duration."*
- *"Override the credit spread input to 250bps and rerun the base case."*
- *"What are the key assumptions in this model?"*
- *"Compare the stagflation and rates_shock_up scenarios."*

---

## Connecting Your Own Model

Docent uses the ports & adapters pattern. To connect your own model:

1. Implement `ScenarioRunner` (executes your model logic)
2. Implement `ModelRepository` (provides your scenarios and schema)
3. Wire them into `PortfolioService`
4. Point the MCP server or CLI at your service

The simplest approach uses the built-in `FunctionalScenarioRunner` and `InMemoryModelRepository`:

```python
from docent.adapters.data.in_memory import FunctionalScenarioRunner, InMemoryModelRepository
from docent.application.service import PortfolioService
from docent.adapters.mcp_server.server import mcp, set_service

def my_model(inputs: dict) -> dict:
    # Your model logic here
    return {"metric_a": ..., "metric_b": ...}

repository = InMemoryModelRepository(schema=MY_SCHEMA, scenarios=MY_SCENARIOS)
runner = FunctionalScenarioRunner(model_fn=my_model, base_inputs=MY_BASE_INPUTS)
service = PortfolioService(runner=runner, repository=repository)
set_service(service)
mcp.run()
```

See `examples/demo_model/model.py` for a complete worked example.

---

## AI Provider Configuration

Set `AI_PROVIDER` in your environment:

| Value | Provider | Required env vars |
|-------|----------|------------------|
| `claude` (default) | Anthropic Claude | `ANTHROPIC_API_KEY` |
| `azure_openai` | Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |

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
- **Adapters** (`adapters/`) — thin translation layers; CLI and MCP server both call `PortfolioService`
- **AI** (`ai/`) — provider adapters and dispatcher; no business logic; no provider-specific code outside its own module

The MCP server and CLI are parallel entry points into the same application layer. They share no code with each other except through `PortfolioService`.
