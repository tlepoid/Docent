# Explicator Model Schema — Bond Portfolio Risk Model (Demo)

> This document describes the demo model bundled with Explicator. When you connect
> your own model, replace this document with an equivalent description of your
> inputs, outputs, and assumptions. This is the primary source of truth for
> Claude's understanding of the domain — write it as if explaining the model to
> a highly intelligent analyst who has never seen it before.

---

## What This Model Does

This is a **simplified fixed-income portfolio risk model** for a mixed bond portfolio
holding government bonds, investment-grade (IG) corporate bonds, and high-yield (HY)
corporate bonds.

Given a set of market inputs (yield levels, credit spreads), it computes:

- **Mark-to-market P&L** relative to the baseline market conditions
- **Duration risk** (DV01 — how much the portfolio loses per 1bp rate rise)
- **Spread risk** (credit DV01 — how much it loses per 1bp of spread widening)
- **Blended portfolio yield** (the weighted average expected return)

The model uses the **modified duration / convexity approximation**, which is standard
for first-order interest rate sensitivity but does not fully reprice individual bonds.

---

## Model Inputs

### Rates Inputs

| Field | Units | Typical Range | Description |
|-------|-------|--------------|-------------|
| `yield_10y` | % | 0.5 – 8.0 | 10-year government benchmark yield. The primary driver of portfolio duration risk. When this rises, bond prices fall. |
| `yield_2y` | % | 0.0 – 8.0 | 2-year government yield. The spread between 2y and 10y defines the shape of the yield curve. |

**Yield curve shape matters**: When `yield_2y > yield_10y` the curve is **inverted**,
which historically precedes recessions. A steep positive curve (10y much higher than 2y)
is associated with economic expansion. The slope affects reinvestment risk and the carry
that short-duration positions earn.

**Sensitivity**: For every 1% (100bp) rise in `yield_10y`, the portfolio loses approximately
`duration × portfolio_value` percent. With duration 6.5 and a £100m portfolio, a 100bp rate
rise costs roughly £6.5m.

### Credit Inputs

| Field | Units | Typical Range | Description |
|-------|-------|--------------|-------------|
| `credit_spread_ig` | % | 0.5 – 4.0 | IG corporate bond spread over the government benchmark. The extra yield investors demand for investment-grade credit risk. |
| `credit_spread_hy` | % | 2.0 – 15.0 | HY corporate bond spread. More volatile; highly sensitive to recession fears and liquidity. |

**Credit spreads in context**:
- **IG spreads** at ~100-150bps are "tight" (risk-on, benign conditions). At 200-300bps they
  indicate moderate stress; above 300bps implies severe market dislocation.
- **HY spreads** at ~300-400bps are tight. The 2008 GFC saw HY spreads reach ~2000bps.
  Spreads above 700bps typically reflect significant default risk concerns.
- Credit spread widening hits the portfolio through both the IG and HY allocations,
  with the HY component contributing disproportionately to P&L volatility.

**Sensitivity**: For every 1% (100bp) spread widening in IG, the portfolio loses approximately
`ig_allocation × duration × portfolio_value` percent. The HY component has similar mechanics
but with higher typical volatility.

### Portfolio Structure Inputs

| Field | Units | Typical Range | Description |
|-------|-------|--------------|-------------|
| `portfolio_duration` | years | 1 – 15 | Modified duration of the whole portfolio. |
| `portfolio_convexity` | — | 0.1 – 2.0 | Second-order curvature; benefits the portfolio in large rate moves. |
| `ig_allocation` | fraction (0–1) | 0 – 1.0 | Fraction allocated to IG corporates. |
| `hy_allocation` | fraction (0–1) | 0 – 0.5 | Fraction allocated to HY corporates. |
| `gov_allocation` | fraction (0–1) | 0 – 1.0 | Fraction allocated to government bonds. |
| `portfolio_value` | £m | — | Portfolio notional value. |

**Constraint**: `ig_allocation + hy_allocation + gov_allocation` should equal 1.

**Duration intuition**: A portfolio with 6.5 years duration behaves like a bullet bond
maturing in ~6.5 years. A 10+ year duration portfolio is very sensitive to rate moves
but earns a higher yield premium. A short-duration portfolio (1-2 years) sacrifices yield
for protection against rate rises.

---

## Model Outputs

### `portfolio_nav` — Net Asset Value (£m)

The portfolio's fair value after marking to market under the scenario's market conditions.
Falls when rates rise or spreads widen. The base case NAV equals `portfolio_value` by
construction (P&L is zero at base inputs).

**Interpretation**: Compare across scenarios to understand absolute value at risk. A NAV
that falls below a regulatory capital threshold is a meaningful warning sign.

### `pnl_total` — Total P&L (£m)

The sum of rate-driven and spread-driven P&L relative to the base case.

- **Positive** = the portfolio gained value in this scenario (e.g., a rates-down flight-to-quality).
- **Negative** = the portfolio lost value (e.g., a rate shock or credit stress).

**Good/bad thresholds**: A loss of £5m or more (5% of a £100m portfolio) is considered severe.

### `pnl_rates` — Rate-Driven P&L (£m)

The portion of total P&L driven purely by changes in government yield levels.
Calculated using the duration-convexity approximation:

```
P&L_rates ≈ -Duration × ΔYield × PV + 0.5 × Convexity × ΔYield² × PV
```

The convexity term is always positive — it means large rate moves hurt less (or help more)
than duration alone would predict.

### `pnl_credit` — Credit-Driven P&L (£m)

The portion of P&L driven by changes in credit spreads:

```
P&L_credit ≈ -(Δspread_IG × Duration × IG_alloc + Δspread_HY × Duration × HY_alloc) × PV
```

In credit stress scenarios this is the dominant driver of losses.

### `dv01` — Dollar Value of 01 (£k per bp)

How much the portfolio gains or loses for each 1bp parallel shift up in government yields.
Always positive (a rate rise hurts a long bond portfolio).

**Formula**: `DV01 = portfolio_value × duration / 10,000`

**Example**: DV01 of 65 means a 100bp rate rise costs ~£6.5m. A 25bp central bank rate
hike costs ~£1.625m.

### `spread_duration` — Spread Duration (years)

The effective duration of the portfolio's credit positions. Measures sensitivity to
a parallel shift in credit spreads.

**Formula**: `spread_duration = (ig_allocation + hy_allocation) × portfolio_duration`

A portfolio 80% invested in credit with 6.5yr duration has a spread duration of ~5.2 years.
A 100bp credit spread widening costs ~5.2% of portfolio value.

### `credit_dv01` — Credit Dollar Value of 01 (£k per bp)

Analogous to DV01 but for credit spread moves. How much the portfolio loses per 1bp of
spread widening across all credit positions.

### `blended_yield_pct` — Blended Portfolio Yield (%)

The portfolio's weighted average all-in yield (government yield + applicable credit spread).
This is the expected return if all bonds are held to maturity with no defaults or prepayments.

Higher blended yield = more credit risk taken. In the base case this is typically 5-6% for a
portfolio with significant IG and some HY allocation.

### `curve_slope_bps` — Yield Curve Slope (bps)

`yield_10y - yield_2y` expressed in basis points. Positive = upward-sloping (normal).
Negative = inverted (recession signal).

### `portfolio_return_pct` — Portfolio Return (%)

Total P&L as a percentage of starting NAV. Allows scenario severity to be compared on a
normalised basis regardless of portfolio size. -5% or worse is considered severe stress.

---

## Scenario Engine

The scenario engine applies **override dictionaries** on top of a set of base inputs.
Scenarios can override any input field. Overrides are merged in the following order
(highest precedence wins):

1. **Call-specific overrides** — provided directly in a `run_scenario` call
2. **Session-level overrides** — set via `override_input` and persist until reset
3. **Scenario definition overrides** — the scenario's own stress parameters
4. **Base model inputs** — the hard-coded market starting point

This layering allows ad-hoc stress testing on top of named scenarios without modifying
the scenario definitions themselves.

### What Scenarios Are Designed For

Each scenario is designed to isolate or combine specific risk factors:

| Scenario | Primary Risk Factor | Use Case |
|----------|-------------------|----------|
| `base_case` | None | Establishes the baseline; all comparisons are relative to this |
| `rates_shock_up` | Duration / rate risk | Central bank tightening, inflation surprise |
| `rates_shock_down` | Duration / flight to quality | Recession, geopolitical crisis |
| `credit_stress` | Spread risk / credit risk | Corporate downturn, liquidity crisis |
| `stagflation` | Both rate + spread risk | Worst-case combination scenario |

---

## Override Mechanism

Session-level overrides are designed for **interactive what-if analysis** — for example,
"what if credit spreads were 50bps wider than in the base case?". They are:

- **Persistent within a session** but not saved to disk
- **Additive on top of scenarios** — they modify the effective input set before the model runs
- **Cleared by `reset_overrides`** — this restores all inputs to model defaults

**Limitations**:
- Overrides only affect inputs defined in the model — unrecognised field names are silently included
  in the `overrides_applied` dict but will not affect model outputs if the model doesn't use them
- Overrides do not validate against `typical_min` / `typical_max` ranges — it is possible to set
  nonsensical values (e.g. negative yields)

---

## Key Assumptions and Caveats

1. **Duration approximation**: The model uses the first-order duration approximation with a
   second-order convexity correction. This is accurate for small to moderate rate moves (±200bp)
   but underestimates losses for large parallel shifts.

2. **Fixed duration**: Duration is treated as a constant input. In reality, duration changes
   as yields move (negative convexity in some instruments). The model does not reprice dynamically.

3. **Parallel shift only**: The model applies the same rate change to all maturities. Real yield
   curves twist and steepen/flatten; this model does not capture curve shape changes independently.

4. **No defaults**: The credit model captures spread widening P&L only — it does not model
   actual defaults, recovery rates, or credit migration.

5. **Relative P&L**: All P&L is measured relative to hard-coded base inputs (4.25% 10yr, 120bp IG,
   350bp HY). If current market conditions differ significantly from these, the P&L numbers will
   not be meaningful in absolute terms.

6. **Allocation constraints**: The model does not enforce that allocations sum to 1. Users setting
   allocation overrides should ensure this manually.
