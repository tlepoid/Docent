"""CLI adapter for Docent.

Provides a command-line interface that calls the same PortfolioService
as the MCP server. No business logic lives here — this is a thin
translation layer from CLI arguments to service method calls.
"""

from __future__ import annotations

import json
import sys

import click

from ...application.service import PortfolioService


def _build_service() -> PortfolioService:
    """Wire up the service from configured adapters."""
    try:
        from examples.demo_model.model import build_repository, build_runner
        repository = build_repository()
        runner = build_runner()
    except ImportError:
        from ...adapters.data.in_memory import _build_stub_wiring
        repository, runner = _build_stub_wiring()

    return PortfolioService(runner=runner, repository=repository)


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Docent — natural language AI interface for portfolio modelling."""
    ctx.ensure_object(dict)
    ctx.obj["service"] = _build_service()


@cli.command("scenarios")
@click.pass_context
def list_scenarios(ctx: click.Context) -> None:
    """List all available scenarios."""
    service: PortfolioService = ctx.obj["service"]
    for s in service.get_available_scenarios():
        click.echo(f"\n{s.name}")
        click.echo(f"  {s.description}")
        click.echo(f"  Stress rationale: {s.stress_rationale}")


@cli.command("run")
@click.argument("scenario_name")
@click.option(
    "--override", "-o", multiple=True, metavar="FIELD=VALUE",
    help="Override an input field for this run, e.g. -o credit_spread=150",
)
@click.pass_context
def run_scenario(ctx: click.Context, scenario_name: str, override: tuple[str, ...]) -> None:
    """Run a named scenario and print results as JSON."""
    service: PortfolioService = ctx.obj["service"]

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
@click.option("--metric", "-m", multiple=True, help="Restrict comparison to this output field")
@click.pass_context
def compare(
    ctx: click.Context,
    scenario_a: str,
    scenario_b: str,
    metric: tuple[str, ...],
) -> None:
    """Compare two scenarios side by side."""
    service: PortfolioService = ctx.obj["service"]
    comparison = service.compare_scenarios(
        scenario_a, scenario_b,
        metrics=list(metric) if metric else None,
    )
    click.echo(json.dumps(comparison.to_dict(), indent=2))


@cli.command("schema")
@click.pass_context
def show_schema(ctx: click.Context) -> None:
    """Print the full model schema as JSON."""
    service: PortfolioService = ctx.obj["service"]
    click.echo(json.dumps(service.get_model_schema().to_dict(), indent=2))


@cli.command("override")
@click.argument("source")
@click.argument("field")
@click.argument("value", type=float)
@click.pass_context
def set_override(ctx: click.Context, source: str, field: str, value: float) -> None:
    """Apply a persistent session override to an input field."""
    service: PortfolioService = ctx.obj["service"]
    click.echo(service.override_input(source, field, value))


@cli.command("reset")
@click.pass_context
def reset_overrides(ctx: click.Context) -> None:
    """Clear all active overrides and restore model defaults."""
    service: PortfolioService = ctx.obj["service"]
    click.echo(service.reset_overrides())
