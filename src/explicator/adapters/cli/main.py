"""CLI adapter for Explicator.

Provides a command-line interface for running scenarios and chatting with an AI.
No business logic lives here — this is a thin translation layer.

Usage::

    explicator --service myapp.model:build_service run base_case
    explicator --service myapp.model:build_service chat
    EXPLICATOR_SERVICE=myapp.model:service explicator compare base stress
"""

from __future__ import annotations

import json
import sys

import click

import explicator
from explicator.application.service import ModelService


def _load_service(path: str | None) -> ModelService:
    """Load the service from a path, or fall back to stub wiring."""
    if path:
        try:
            return explicator.load_service(path)
        except Exception as exc:
            raise click.UsageError(
                f"Could not load service from '{path}': {exc}"
            ) from exc

    from explicator.adapters.data.in_memory import _build_stub_wiring

    repository, runner = _build_stub_wiring()
    return ModelService(runner=runner, repository=repository)


@click.group()
@click.option(
    "--service",
    "service_path",
    envvar="EXPLICATOR_SERVICE",
    default=None,
    help="Service path: 'module:attribute'. Also reads EXPLICATOR_SERVICE env var.",
)
@click.pass_context
def cli(ctx: click.Context, service_path: str | None) -> None:
    """Explicator — natural language AI interface for scenario-driven modelling."""
    ctx.ensure_object(dict)
    ctx.obj["service"] = _load_service(service_path)


@cli.command("scenarios")
@click.pass_context
def list_scenarios(ctx: click.Context) -> None:
    """List all available scenarios."""
    service: ModelService = ctx.obj["service"]
    for s in service.get_available_scenarios():
        click.echo(f"\n{s.name}")
        click.echo(f"  {s.description}")
        click.echo(f"  Stress rationale: {s.stress_rationale}")


@cli.command("run")
@click.argument("scenario_name")
@click.option(
    "--override",
    "-o",
    multiple=True,
    metavar="FIELD=VALUE",
    help="Override an input field for this run, e.g. -o yield_10y=5.0",
)
@click.pass_context
def run_scenario(
    ctx: click.Context, scenario_name: str, override: tuple[str, ...]
) -> None:
    """Run a named scenario and print results as JSON."""
    service: ModelService = ctx.obj["service"]

    overrides: dict = {}
    for o in override:
        if "=" not in o:
            click.echo(f"Invalid override format '{o}'. Use FIELD=VALUE.", err=True)
            sys.exit(1)
        field, value = o.split("=", 1)
        try:
            overrides[field.strip()] = float(value.strip())
        except ValueError:
            click.echo(f"Override value must be numeric: '{value}'", err=True)
            sys.exit(1)

    result = service.run_scenario(scenario_name, overrides=overrides or None)
    click.echo(json.dumps(result.to_dict(), indent=2))


@cli.command("compare")
@click.argument("scenario_a")
@click.argument("scenario_b")
@click.option(
    "--metric", "-m", multiple=True, help="Restrict comparison to this output field"
)
@click.pass_context
def compare(
    ctx: click.Context,
    scenario_a: str,
    scenario_b: str,
    metric: tuple[str, ...],
) -> None:
    """Compare two scenarios side by side."""
    service: ModelService = ctx.obj["service"]
    comparison = service.compare_scenarios(
        scenario_a,
        scenario_b,
        metrics=list(metric) if metric else None,
    )
    click.echo(json.dumps(comparison.to_dict(), indent=2))


@cli.command("schema")
@click.pass_context
def show_schema(ctx: click.Context) -> None:
    """Print the full model schema as JSON."""
    service: ModelService = ctx.obj["service"]
    click.echo(json.dumps(service.get_model_schema().to_dict(), indent=2))


@cli.command("override")
@click.argument("source")
@click.argument("field")
@click.argument("value", type=float)
@click.pass_context
def set_override(ctx: click.Context, source: str, field: str, value: float) -> None:
    """Apply a persistent session override to an input field."""
    service: ModelService = ctx.obj["service"]
    click.echo(service.override_input(source, field, value))


@cli.command("reset")
@click.pass_context
def reset_overrides(ctx: click.Context) -> None:
    """Clear all active overrides and restore model defaults."""
    service: ModelService = ctx.obj["service"]
    click.echo(service.reset_overrides())


@cli.command("chat")
@click.argument("question", required=False)
@click.pass_context
def chat(ctx: click.Context, question: str | None) -> None:
    """Chat with an AI about the model. Omit QUESTION for interactive mode."""
    service: ModelService = ctx.obj["service"]
    try:
        explicator.run_chat(service, question=question)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
