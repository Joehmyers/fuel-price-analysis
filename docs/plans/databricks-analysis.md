# Plan: Test fuel prices as a demand feature inside the AA Databricks environment

> **Status:** Draft
> **Date:** 2026-11-17

Spec: none. The what and why are in
[docs/research/desnz-retreat.md](../research/desnz-retreat.md) and
[reports/regional-variation-answer.md](../../reports/regional-variation-answer.md).

## Overview

Stage 1 (this repo, public data only) is done. Stage 2 moves the code into the
AA Databricks workspace (the shared data platform where the forecasting team
runs notebooks and jobs), joins public fuel prices to breakdown demand, and
tests whether price changes improve the daily forecast. The plan is built on
four findings from stage 1:

- Use the national UK price (DESNZ weekly, petrol and diesel). Regional and
  country features are parked: there is no country history before February 2026.
- People respond to price changes, not levels, so features are changes at lags
  of weeks, with rises and falls separate.
- Use only prices already public at the forecast time (`published_at`).
- The cleanest effect is likely small (reported elasticities of -0.07 to -0.29,
  unverified), so the plan checks first whether the data can detect it.

No AA data enters this repo. Only code, documents and public data move in one
direction (out of this repo, into Databricks). Results leave Databricks only as
aggregate numbers cleared for sharing.

## Definitions

- **Databricks:** the AA's cloud platform for data, notebooks and scheduled jobs.
- **Delta table:** a table stored in Databricks with a change history.
- **MLflow:** the tool the team uses to log each model run, its settings and its
  scores.
- **Created demand:** jobs raised when members contact the AA, dated by creation
  and placed by breakdown location, de-duplicated. The team's earlier decision
  (Notion, "Decide the demand measure") uses it because it has the least supply
  distortion.
- **Forecast origin:** the moment a forecast is made. Features may use only what
  was public by then.
- **Backtest:** replaying the forecast over past dates, each time using only the
  data available at that origin.
- **WAPE:** weighted absolute percentage error: total absolute error divided by
  total demand. Lower is better.
- **Baseline:** the team's current daily forecast, including its adjustment for
  weather and school holidays ("normalisation").
- **Out-of-fuel jobs:** call-outs whose reason code says the vehicle ran out of
  fuel (or charge).

## Steps

### A. Move the code and the public data

The public data is committed in `datasets/public/` (see its README), so no
download is needed. [DATABRICKS.md](../../DATABRICKS.md) is the entry point for
whoever works in Databricks.

- [x] A1. Commit the two public tables (`desnz_real.parquet`, `cpi_monthly.parquet`,
      132 KB in all) with a column guide, and a test that guards them
      (`tests/test_public_snapshot.py`).
- [ ] A2. Upload the repo to Databricks as a Git folder or a zip. Confirm the tests
      pass there (`python -m pytest -q`). Fix any path difference in `src/config.py`.
- [ ] A3. Write the weekly prices to a Delta table `fuel_prices_weekly` with
      `published_at` kept. Note that 1,306 of 2,448 CPI release times are assumed
      (months before Nov 2015).
- [ ] A4. Only if the data needs refreshing: ask the admin whether a cluster can
      reach gov.uk and ons.gov.uk, then run the fetch and clean scripts. Record
      the answer in `docs/sources.md`.

### B. Prepare the demand side (inside Databricks only)

- [ ] B1. Build a daily created-demand table: national total, plus a split by reason
      code (out of fuel, flat battery, other) and, only if volumes allow, by
      country. Use creation date and breakdown location. Record the history
      length: the first day, last day and any gaps.
- [ ] B2. Compute the overlap with the fuel series. The longer the history, the
      more price shocks it holds (2008: 4 weeks with a move over 3p; 2022: 13;
      2026: 14). Write down how many separate shocks the demand history
      covers. This sets what we can claim.
- [ ] B3. Fetch Department for Transport traffic statistics (public) for the same
      period, to test the link from price to traffic to breakdowns.
- [ ] B4. Load the baseline's own residuals and inputs: the daily forecast, its weather
      and school-holiday adjustment, and its backtest errors. The fuel features
      must add to the baseline, not repeat what weather already explains.

### C. Build the price features

- [ ] C1. Add `src/features/price_features.py` with a function
      `fuel_features(prices, origin)` that returns, for a forecast origin, only the
      prices with `published_at <= origin`. Features: weekly change; change over 4
      and 8 weeks; rises and falls as two separate series; lags of 0 to 12 weeks;
      the diesel minus petrol difference; the equal-weight index of the two fuels.
      Level features (raw and adjusted) are built only as comparison.
- [ ] C2. Turn weekly prices into a daily series: a price is visible from its
      `published_at`, not from the Monday it covers (about 33 hours after the Monday begins).
- [ ] C3. Write `tests/test_price_features.py`: (a) a forecast origin before
      Tuesday 09:30 UK sees the previous week; (b) rises and falls sum to the
      change; (c) lags never read a later week. Test first, then the code.

### D. Experiments

Pre-register the questions and the tests below before looking at results, and
log every run in MLflow. Run them in this order; stop at the first that cannot
be answered.

- [ ] D0. **Can we detect it?** Take the demand series and the reported elasticities
      (-0.07 to -0.29 for traffic). A 20% price rise cuts traffic by 1.4% to 5.8%.
      Using the daily noise of demand after weather and calendar adjustment, work
      out the smallest effect the data can reveal. If it exceeds the plausible
      effect, report that and stop.
- [ ] D1. **Out-of-fuel jobs against price changes** (the most direct link). Count
      model (negative binomial: a regression for counts with extra spread) with
      calendar, weather and trend terms, plus the lagged price changes. Report the
      effect of a 10% rise at each lag, with 95% intervals. Placebo check: the
      same model with prices shifted 8 weeks into the future must show no effect.
- [ ] D2. **Does it improve the forecast?** Backtest the baseline with and without
      the fuel features. Expanding window, a new origin every 7 days for at least
      the last 2 years of the history. Score WAPE overall and in shock weeks
      (weeks with a UK price move over 3p). Compare with a paired test on the
      daily errors, using a block bootstrap (resampling runs of days, not single
      days) because errors are linked from day to day.
- [ ] D3. **Shock episodes.** For 2022 and 2026 (and 2008 if the history reaches
      it), compare actual demand with the baseline forecast in the 12 weeks
      after the price began to rise. Look for a fall in demand (less driving) and a
      rise in out-of-fuel jobs. Report each episode separately, not pooled.
- [ ] D4. **Delayed servicing.** Test whether breakdowns per vehicle-mile (using
      the traffic data from B3) rise 2 to 6 months after a rise in price. This
      follows from the RAC survey result; it is a hypothesis, not a finding.
- [ ] D5. **Raw against adjusted price, and changes against levels.** Repeat D1 and
      D2 with the adjusted price (`real_pence_asof`) and with levels, to answer
      the question in Notion. Expect little difference in weekly changes (they
      correlate 0.95).
- [ ] D6. **Country split (conditional).** Only if call-outs are available by
      country and Northern Ireland has enough volume, repeat D1 with the country
      price gap changes. Otherwise drop it.

### E. Decide and hand over

- [ ] E1. Set the success rule before running D2, with the forecasting lead. Proposed
      for discussion, not agreed: keep a fuel feature if it lowers WAPE in shock
      weeks by at least 1% of itself, does not raise WAPE overall, and its D1
      interval excludes zero at a lag the traffic evidence supports.
- [ ] E2. Write the results as a research note in `docs/research/` with the same
      structure as the stage 1 note (what was tested, numbers, limits). Aggregate
      numbers only.
- [ ] E3. If the rule is met, add the features to the team's pipeline: a weekly job
      that runs Tuesday after 10:00 UK, writes `fuel_prices_weekly`, and logs to
      MLflow. If DESNZ is late, carry the last price forward and flag the row.
      Record the choice as a decision (`/decision`).
- [ ] E4. Run `ops/check.sh`; fix any failures.
- [ ] E5. Commit: `add fuel price features and Databricks analysis notebooks`.

## Risks and how the plan handles them

| Risk | Handling |
|---|---|
| Few independent shocks (about 3) in the history, so low power | D0 states the smallest detectable effect first; D3 reports each shock alone |
| Shocks overlap weather and season (March 2026 rise) | Fit the baseline's weather and calendar terms first; check shock weeks against matching weeks a year earlier |
| Testing many lags finds false positives | Fix the lag set in advance (0 to 12 weeks); correct for the number tested; keep the last 6 months as a final untouched test |
| Look-ahead: using a price before it was public | `published_at` rule, tests in C3, and the placebo in D1 |
| Fuel is part of CPI, so adjusted prices partly contain themselves | Treat D5 as a robustness check, not the main result |
| Half the DESNZ release times are assumed (09:30 UK) | Test the effect of shifting them by one day; the weekly step is large compared with a few hours |
| AA data leaks into the repo | Keep data and notebook outputs in Databricks; commit code only; review diffs before pushing |

## Files changed

| File | Change |
|------|--------|
| `src/features/price_features.py` | new: weekly prices to as-of daily change features |
| `tests/test_price_features.py` | new: visibility, lag and rise/fall tests |
| `notebooks/databricks/01_load_fuel_prices.py` | new: write `fuel_prices_weekly` (code only, no data) |
| `notebooks/databricks/02_detectability.py` | new: D0 |
| `notebooks/databricks/03_experiments.py` | new: D1 to D6, logging to MLflow |
| `docs/sources.md` | add Databricks network answers (A1) and the DfT traffic source (B3) |
| `docs/research/databricks-results.md` | new: results note (E2) |
| `docs/decisions/D-0004-*.md` | new, if the rule is met (E3) |

## Verification

```bash
ops/check.sh
```

In Databricks: the backtest runs from a single notebook with a fixed seed and
reproduces its own scores within 0.01 percentage points; the placebo run in D1
shows no effect; and `fuel_prices_weekly` has no row with `published_at` later
than its own origin in the feature table.

## What I need from you

- Databricks access, and the answers to A1.
- The name of the created-demand table and its history length (B1).
- Whether reason codes (out of fuel) and country are available (D1, D6).
- The forecasting lead's view on the success rule in E1.

---

_Related research: [DESNZ fall-back note](../research/desnz-retreat.md), [traffic elasticity](../research/traffic-elasticity.md)._
