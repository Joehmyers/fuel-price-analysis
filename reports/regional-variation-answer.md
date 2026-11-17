# Is regional fuel price variation worth using as a forecasting feature?

Data: station prices from FuelCosts (a copy of the official Fuel Finder feed),
9 Feb to 17 Nov 2026, about 7,500 stations a day. Gaps below use 15 Mar onward,
once station coverage settled. All figures are pence per litre (p).

## Short answer

**Mostly no, with one exception.** Across Great Britain, regions sit within
about 2 p of the UK average, which is under 1.5% of the price. Northern Ireland
is the exception: it is 6 p cheaper than average for E10 petrol and 8 p for
standard diesel, and its gap is growing. Whether a regional feature earns its
place depends on how much call-out demand moves with a 1 to 2 p difference.
This data cannot answer that; stage 2 can. Published traffic elasticities put the
most a Great Britain regional gap could explain at about 0.1% to 0.6% of traffic
(see "What the spread could mean for traffic").

## The numbers (E10 petrol; standard diesel in brackets)

- **Great Britain, average gap to the UK price.** South East +1.5 p (+1.8),
  Scotland +1.4 (+1.3), North East -1.3 (-0.7), Yorkshire -1.2 (-0.6). On 98%
  (96%) of region-days, the gap is smaller than 2 p.
- **Northern Ireland.** Average gap -6.1 p (-7.8). It started at -3.3 p in March
  and reached -10.8 p (-9.3) by mid-November.
- **Spread across the 12 regions.** The standard deviation averages 2.1 p
  (2.5), and the top-to-bottom range 7.8 p (9.5). Without Northern Ireland the
  range of region averages is 3.1 p (2.8).
- **Compared with price moves.** The UK price changed by 2.4 p in a typical week
  (3.7 p for diesel), and by up to 5.4 p (10.2 p). The regional gaps move far
  less than that: day to day, a region's gap varies by only 0.3 to 0.6 p (standard deviation) outside Northern Ireland.

## Do the gaps widen when prices move?

Not in Great Britain. In the weeks with the biggest UK price moves, the spread
across regions was the same or slightly narrower (E10: 2.0 p against 2.1 p in
calm weeks). The link between price moves and spread is weakly negative
(correlation -0.27 for E10, -0.53 for standard diesel). The slope of each
region's gap on the UK weekly change is within 0.05 p per p for every region,
bar Northern Ireland, where it is +0.06 (E10) and +0.15 (premium diesel): the
gap widens when the UK price falls, which is what happened in October and
November.

## Weighting choice

The UK average is the mean over all stations, so it follows where pumps are.
A plain mean of the 12 region averages differs from it by 0.3 p for E10 and
standard diesel, and 1.0 to 1.4 p for E5 and premium diesel, so the choice
matters little for the main fuels. The spread uses the 12 region averages with
equal weight, because each region is one unit in a forecast. Station count is a
rough stand-in for fuel sold; sales by region would be better, and we do not
have them.

## Check against the official weekly figure (DESNZ)

On 41 Mondays, the FuelCosts UK mean is 0.7 p above the DESNZ figure for both
petrol (E10 against "unleaded") and diesel. The two move together: correlation
0.99 for levels and 0.92 to 0.93 for weekly changes. The gap is not constant. It
reached 4.3 p (petrol) and 6.7 p (diesel) on 23 March, during the sharp rise,
and was -3.1 p for petrol on 16 November. A likely cause is timing, since DESNZ
may average a different part of the week, but I could not confirm that. E5 was
left out: DESNZ "unleaded" is mostly E10, and E5 sells about 18 p higher.

## Limits

- **Short history.** Nine months, and the official feed started in February 2026.
  No year-on-year seasonal pattern can be checked.
- **Few shocks.** One sharp rise (March) and one fall (October to November). The
  finding that gaps do not widen rests on those two episodes.
- **Early data are thinner.** Station coverage grew from 5,300 to 7,600 in
  Feb to Mar, so we start the gaps in mid-March.
- **Northern Ireland trend.** It could be real, or a change in which stations
  report. We did not test the second explanation.
- **Prices are for the day, not demand.** A 2 p regional gap says nothing yet
  about call-outs.
- **Long record only nationally.** DESNZ gives UK petrol and diesel since 2003
  but no regions.

## Which fuels to carry into stage 2

Use two fuel series: **E10 petrol** and **standard diesel**.

- E10 and E5 weekly price changes correlate at 0.97, and standard and premium
  diesel at 0.98, so the second fuel in each pair adds nothing.
- Petrol and diesel correlate at 0.89 to 0.92 in weekly changes, yet differ
  enough to keep apart: for each 1 p E10 moves, standard diesel moves about
  1.45 p, and the diesel premium over E10 ranged from 13.5 p to 33.4 p.
- Northern Ireland's gap behaves the same way: petrol gaps move together
  (0.98), diesel gaps move together (0.95), but a petrol gap and a diesel gap
  correlate only 0.3 to 0.4.
- The two series are correlated, so a model with both can give unstable
  coefficients. Test each alone, or use one fuel's level plus the diesel minus
  petrol difference.

## What the spread could mean for traffic

Elasticity is the percentage change in traffic for a 1% change in price. The
figures below come from a research report cited in chat; we have not opened the
papers (see `docs/research/traffic-elasticity.md`). Reported UK values run from
-0.07 (HM Treasury, short run) to -0.29 (Goodwin and others, long run).

Turn the regional gaps into percentages of the price, then multiply by the
elasticity (E10 at 161 p, standard diesel at 185 p, 15 Mar to 17 Nov 2026):

| | Price gap | Traffic effect at -0.07 | at -0.29 |
|---|---|---|---|
| E10, top to bottom across Great Britain (3.1 p) | 1.9% | 0.13% | 0.56% |
| E10, Northern Ireland against the UK (6.1 p) | 3.8% | 0.27% | 1.1% |
| Diesel, top to bottom across Great Britain (2.8 p) | 1.5% | 0.11% | 0.44% |
| Diesel, Northern Ireland against the UK (7.8 p) | 4.2% | 0.29% | 1.2% |
| For scale: the UK price rise from March to October | about 24% | 1.6% to 1.7% | 6.8% to 7.0% |

Read it this way:

- A Great Britain regional gap is worth at most about 0.1% to 0.6% of traffic.
  That is about one twelfth of the effect of the national price swing, and far
  below the weather or school holidays.
- Northern Ireland is the one case that could show up, at up to about 1%.
- This is a ceiling, not a forecast. Regional gaps are persistent, so people
  there have adapted already; the elasticities describe how traffic reacts to a
  change in price, not why one region differs from another. Drivers also cross
  regional borders. Different roads, fleets and incomes would swamp a 0.1%
  effect.
- The research suggests a bigger lever may be the national price level. Its
  effect builds up over weeks, and delayed servicing could raise breakdowns per
  mile months later. Stage 2 should test a lagged national price, with the
  regional gap as a second, smaller candidate.
- No study links UK fuel prices to roadside-assistance demand. Only your own
  call-out data, split by reason code (such as out of fuel), can show it.

## Inflation (CPI)

Not needed here: gaps are in pence on the same day, so general price rises
cancel out. CPI rose 2.9% from February to September 2026 (140.1 to 144.1),
against a rise of over 20% in E10 (132 p in February, 162 p in late August). It would matter in stage 2 if the long 2003 onward
DESNZ series is used, to put old prices in today's money. Fuel is part of CPI,
and each month's figure comes about three weeks after the month ends, so use
the release dates already stored.

## Charts

- `gap_by_region_E10.png`, `gap_by_region_diesel_standard.png`: gap to the UK
  average by region over time.
- `spread_vs_price_E10.png`, `spread_vs_price_diesel_standard.png`: spread
  across regions, below the UK price.

Sources and licences: see `docs/sources.md` (Open Government Licence v3.0).
