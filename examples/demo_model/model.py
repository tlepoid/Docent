"""Demo model: Bond Portfolio Risk Model.

A simplified fixed-income portfolio model for demonstrating Docent.
Shows how to implement the ScenarioRunner and ModelRepository ports
using the in-memory adapters provided by Docent.

Not production-ready — designed to be readable and illustrative.
"""

from __future__ import annotations

from typing import Any

from docent.adapters.data.in_memory import FunctionalScenarioRunner, InMemoryModelRepository
from docent.domain.models import (
    InputField,
    ModelSchema,
    OutputField,
    ScenarioDefinition,
)

# ------------------------------------------------------------------
# Base inputs — market conditions and portfolio structure
# ------------------------------------------------------------------

BASE_INPUTS: dict[str, Any] = {
    "yield_10y": 4.25,           # 10-year government yield (%)
    "yield_2y": 4.80,            # 2-year government yield (%)
    "credit_spread_ig": 1.20,    # IG credit spread over govts (%)
    "credit_spread_hy": 3.50,    # HY credit spread over govts (%)
    "portfolio_duration": 6.5,   # Portfolio modified duration (years)
    "portfolio_convexity": 0.45, # Portfolio convexity
    "ig_allocation": 0.65,       # Fraction allocated to IG credit
    "hy_allocation": 0.15,       # Fraction allocated to HY credit
    "gov_allocation": 0.20,      # Fraction allocated to government bonds
    "portfolio_value": 100.0,    # Portfolio notional value (£m)
}


# ------------------------------------------------------------------
# Model function
# ------------------------------------------------------------------

def bond_portfolio_model(inputs: dict[str, Any]) -> dict[str, float]:
    """
    Simplified bond portfolio pricing and risk model.

    Uses duration/convexity approximation to compute mark-to-market P&L
    and key risk metrics for a mixed government/IG/HY bond portfolio.
    """
    pv = inputs["portfolio_value"]
    dur = inputs["portfolio_duration"]
    cvx = inputs["portfolio_convexity"]
    ig_alloc = inputs["ig_allocation"]
    hy_alloc = inputs["hy_allocation"]
    gov_alloc = inputs["gov_allocation"]

    yield_10y = inputs["yield_10y"] / 100
    yield_2y = inputs["yield_2y"] / 100
    cs_ig = inputs["credit_spread_ig"] / 100
    cs_hy = inputs["credit_spread_hy"] / 100

    # Yield curve slope (positive = normal / upward sloping)
    curve_slope_bps = (inputs["yield_10y"] - inputs["yield_2y"]) * 100

    # All-in yields by sector
    yield_ig = yield_10y + cs_ig
    yield_hy = yield_10y + cs_hy
    yield_gov = yield_10y

    # Blended portfolio yield (weighted average)
    blended_yield = (
        gov_alloc * yield_gov
        + ig_alloc * yield_ig
        + hy_alloc * yield_hy
    )

    # DV01: dollar value of 1bp rate move (£k per bp)
    dv01 = pv * dur / 10_000

    # P&L from rate moves (vs hard-coded base of 4.25%)
    base_yield_10y = 4.25 / 100
    delta_yield = yield_10y - base_yield_10y
    pnl_rates = (-dur * delta_yield + 0.5 * cvx * delta_yield ** 2) * pv

    # P&L from credit spread moves (vs hard-coded base of 120bps / 350bps)
    base_cs_ig = 1.20 / 100
    base_cs_hy = 3.50 / 100
    pnl_credit = (
        -(cs_ig - base_cs_ig) * dur * ig_alloc * pv
        + -(cs_hy - base_cs_hy) * dur * hy_alloc * pv
    )

    total_pnl = pnl_rates + pnl_credit
    portfolio_nav = pv + total_pnl

    # Spread duration: effective duration of credit positions
    spread_duration = (ig_alloc + hy_alloc) * dur

    # Credit DV01: £ gained/lost per 1bp of spread move
    credit_dv01 = spread_duration * (ig_alloc + hy_alloc) * pv / 10_000

    return {
        "portfolio_nav": round(portfolio_nav, 4),
        "pnl_total": round(total_pnl, 4),
        "pnl_rates": round(pnl_rates, 4),
        "pnl_credit": round(pnl_credit, 4),
        "dv01": round(dv01, 4),
        "spread_duration": round(spread_duration, 4),
        "credit_dv01": round(credit_dv01, 6),
        "blended_yield_pct": round(blended_yield * 100, 4),
        "curve_slope_bps": round(curve_slope_bps, 1),
        "portfolio_return_pct": round(total_pnl / pv * 100, 4),
    }


# ------------------------------------------------------------------
# Scenario definitions
# ------------------------------------------------------------------

SCENARIOS: list[ScenarioDefinition] = [
    ScenarioDefinition(
        name="base_case",
        description="Current market conditions — no shocks applied.",
        stress_rationale="Baseline against which all stress scenarios are measured.",
        overrides={},
    ),
    ScenarioDefinition(
        name="rates_shock_up",
        description="Parallel shift up in rates by 100bps across the curve.",
        stress_rationale=(
            "Tests portfolio sensitivity to a rapid central bank tightening cycle. "
            "Historically relevant: Fed hiking cycles of 2004-2006 and 2022-2023."
        ),
        overrides={
            "yield_10y": BASE_INPUTS["yield_10y"] + 1.0,
            "yield_2y": BASE_INPUTS["yield_2y"] + 1.0,
        },
    ),
    ScenarioDefinition(
        name="rates_shock_down",
        description="Parallel shift down in rates by 100bps — flight to safety.",
        stress_rationale=(
            "Models a risk-off flight to quality where government bond yields fall sharply. "
            "Relevant during recessions, geopolitical crises, or financial system stress."
        ),
        overrides={
            "yield_10y": BASE_INPUTS["yield_10y"] - 1.0,
            "yield_2y": BASE_INPUTS["yield_2y"] - 1.0,
        },
    ),
    ScenarioDefinition(
        name="credit_stress",
        description="IG spreads widen to 250bps; HY spreads widen to 700bps.",
        stress_rationale=(
            "Models a credit market dislocation consistent with a moderate recession. "
            "IG at 250bps and HY at 700bps were observed during the 2008-2009 GFC."
        ),
        overrides={
            "credit_spread_ig": 2.50,
            "credit_spread_hy": 7.00,
        },
    ),
    ScenarioDefinition(
        name="stagflation",
        description="Rates rise 150bps and credit spreads widen simultaneously.",
        stress_rationale=(
            "The worst of both worlds for fixed income: duration losses from rising rates "
            "compounded by credit losses from spread widening. Stylised 1970s-style stagflation."
        ),
        overrides={
            "yield_10y": BASE_INPUTS["yield_10y"] + 1.5,
            "yield_2y": BASE_INPUTS["yield_2y"] + 1.5,
            "credit_spread_ig": 2.00,
            "credit_spread_hy": 5.50,
        },
    ),
]


# ------------------------------------------------------------------
# Schema
# ------------------------------------------------------------------

SCHEMA = ModelSchema(
    name="Bond Portfolio Risk Model (Demo)",
    description=(
        "A simplified fixed-income portfolio risk model that computes mark-to-market "
        "P&L, duration risk (DV01), spread risk (credit DV01), and blended yield "
        "for a mixed government / IG / HY bond portfolio."
    ),
    inputs=[
        InputField(
            name="yield_10y",
            source="rates",
            description="10-year government benchmark yield.",
            units="%",
            typical_min=0.5,
            typical_max=8.0,
            current_value=BASE_INPUTS["yield_10y"],
        ),
        InputField(
            name="yield_2y",
            source="rates",
            description=(
                "2-year government yield. The spread between 2y and 10y defines "
                "the shape of the yield curve — an inverted curve (2y > 10y) "
                "is a classic recession indicator."
            ),
            units="%",
            typical_min=0.0,
            typical_max=8.0,
            current_value=BASE_INPUTS["yield_2y"],
        ),
        InputField(
            name="credit_spread_ig",
            source="credit",
            description=(
                "Investment-grade corporate bond spread over the government benchmark. "
                "Reflects the additional yield investors demand for IG credit risk. "
                "Widens during market stress; tightens during risk-on periods."
            ),
            units="%",
            typical_min=0.50,
            typical_max=4.00,
            current_value=BASE_INPUTS["credit_spread_ig"],
        ),
        InputField(
            name="credit_spread_hy",
            source="credit",
            description=(
                "High-yield corporate bond spread over the government benchmark. "
                "More volatile than IG spreads; highly sensitive to recession risk "
                "and liquidity conditions."
            ),
            units="%",
            typical_min=2.00,
            typical_max=15.00,
            current_value=BASE_INPUTS["credit_spread_hy"],
        ),
        InputField(
            name="portfolio_duration",
            source="portfolio",
            description=(
                "Modified duration of the overall portfolio in years. "
                "Measures linear interest rate sensitivity: a duration of 6.5 means "
                "a 1% rate rise costs approximately 6.5% of portfolio value."
            ),
            units="years",
            typical_min=1.0,
            typical_max=15.0,
            current_value=BASE_INPUTS["portfolio_duration"],
        ),
        InputField(
            name="ig_allocation",
            source="portfolio",
            description="Fraction of portfolio allocated to IG corporate bonds (0–1).",
            units="fraction",
            typical_min=0.0,
            typical_max=1.0,
            current_value=BASE_INPUTS["ig_allocation"],
        ),
        InputField(
            name="hy_allocation",
            source="portfolio",
            description=(
                "Fraction of portfolio allocated to HY corporate bonds (0–1). "
                "Higher allocation increases credit spread sensitivity and default risk."
            ),
            units="fraction",
            typical_min=0.0,
            typical_max=0.5,
            current_value=BASE_INPUTS["hy_allocation"],
        ),
    ],
    outputs=[
        OutputField(
            name="portfolio_nav",
            description="Portfolio net asset value after marking to market.",
            units="£m",
            interpretation=(
                "The current fair value. Falls when rates rise or spreads widen; "
                "rises in flight-to-quality / rates-down scenarios."
            ),
        ),
        OutputField(
            name="pnl_total",
            description="Total mark-to-market P&L relative to the base case.",
            units="£m",
            interpretation=(
                "Positive = portfolio gained value. Negative = loss. "
                "Sum of rate-driven and spread-driven components."
            ),
            good_threshold=0.0,
            bad_threshold=-5.0,
        ),
        OutputField(
            name="dv01",
            description="Dollar value of one basis point — rate sensitivity.",
            units="£k per bp",
            interpretation=(
                "How much the portfolio gains or loses for each 1bp move in rates. "
                "A DV01 of £65k means a 100bp rate rise costs ~£6.5m."
            ),
        ),
        OutputField(
            name="spread_duration",
            description="Spread duration of credit positions.",
            units="years",
            interpretation=(
                "Higher spread duration means greater sensitivity to credit spread widening. "
                "A portfolio with 5yr spread duration loses ~5% if spreads widen 100bps."
            ),
        ),
        OutputField(
            name="blended_yield_pct",
            description="Weighted average yield across all portfolio holdings.",
            units="%",
            interpretation=(
                "The expected return if held to maturity with no defaults. "
                "Higher yield compensates for more credit risk."
            ),
        ),
        OutputField(
            name="portfolio_return_pct",
            description="Total P&L expressed as a percentage of starting NAV.",
            units="%",
            interpretation=(
                "Normalised return — useful for comparing stress severity across scenarios "
                "regardless of portfolio size."
            ),
            good_threshold=0.0,
            bad_threshold=-5.0,
        ),
    ],
    assumptions=[
        "Duration and convexity are fixed parameters — they do not reprice dynamically.",
        "Credit P&L uses a duration-weighted spread DV01 approximation.",
        "The model does not account for convexity in credit spreads.",
        "No default probability or credit migration modelling is included.",
        "All P&L is computed relative to the hard-coded base inputs, not live MTM.",
        "Allocations (ig_allocation, hy_allocation, gov_allocation) must sum to 1.",
    ],
    caveats=[
        "This is a demonstration model only — not suitable for production risk management.",
        "Real portfolios require full position-level pricing, not a duration approximation.",
        "Replace BASE_INPUTS with live market data feeds before real use.",
    ],
)


# ------------------------------------------------------------------
# Factory functions
# ------------------------------------------------------------------

def build_repository() -> InMemoryModelRepository:
    """Build the model repository for the demo bond portfolio model."""
    return InMemoryModelRepository(schema=SCHEMA, scenarios=SCENARIOS)


def build_runner() -> FunctionalScenarioRunner:
    """Build the scenario runner for the demo bond portfolio model."""
    return FunctionalScenarioRunner(
        model_fn=bond_portfolio_model,
        base_inputs=BASE_INPUTS,
    )
