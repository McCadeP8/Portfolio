# Snap Prep

Working area for the 2026 fantasy-football draft.

## Projection baseline

The starting projections were copied from the neighboring `Smack_Talkers_DP`
project on September 3, 2026.

- `data/base/player_stat_projections_2026.csv`: normalized player projections in
  consensus, high, and low scenarios, including the custom league scoring total.
- `data/base/projection_rankings_2026.csv`: rankings derived from the custom
  projection model.
- `data/base/projection_assumptions_2026.json`: scoring and modeling assumptions.
- `data/raw/fantasypros/`: untouched position-level FantasyPros projection exports
  used to produce the normalized baseline.

The source files remain unchanged so future Snap-specific scoring, tiers, and
draft strategy can be layered on top without losing provenance.

## Chopped-league draft model

`chopped_league_draft_rankings_2026.csv` is the 252-player draft board for 18
teams with nine starters and five bench spots. The player pool contains 27 QBs,
81 RBs, 81 WRs, 27 TEs, 18 kickers, and 18 defenses. This keeps the previous
board's membership fixed for a controlled comparison; it does not claim these
are the optimal positional draft counts. The original 162-starter weekly CSV
is unchanged. Prior draft rankings are preserved in
`data/base/previous_chopped_rankings_2026.csv`.

The replacement model uses 512 seeded league worlds and 129,024 paired player
counterfactuals. Each world drafts 18 distinct 14-player rosters, selects legal
lineups, eliminates the lowest scorer each week, and releases that team's entire
roster for the following week's waivers. Two conditional IR slots are modeled.
There are 18 teams in Week 1 and two in Week 17, not 18 playing weeks.

For each drafted player, a matched run replaces him with an initially undrafted
same-position player. Teammates, draft, waiver priority, and NFL outcomes are held
fixed. The removed player cannot be reacquired. The ranking score is the gain in
expected weeks reached (capped at 17), plus eight times the gain in championship
probability. Eight is an explicit preference weight, not a fitted parameter.
There are no QB/TE rank bonuses, named-player ranking boosts, or K/DST discounts.
This measures value over free replacement, not the opportunity cost of choosing
one available player instead of another at a particular draft pick.

Player outcomes combine low/consensus/high triangular season draws, persistent
lognormal uncertainty, weekly volatility, and generic injury spells. Low/high
are scenario bounds before the extra uncertainty, not confidence intervals.
Managers only see baseline projections, current availability, and prior weekly
results; current-week realized scores are never used to choose lineups. Forecasts
update using six prior-equivalent games. Byes score zero. Conditional start rates
refer to the player's original team while it is alive and the player is available,
not the probability of being among the league's final two best players.

Drafts use randomized market-rank preferences, positional completion constraints,
at most two QB/TE per team, and K/DST in the final two rounds. Market ranks come
from the copied `league_reference_2026.csv` where available; the prior board is
the fallback, including Jacobs/Lloyd draft context. Waivers use rotating random
priority and one successful improvement per team per week, with current lineup,
future lineup, and bench projection weights of 1, 0.25, and 0.04. This is a
bounded management policy, not optimal play or FAAB bidding.

The CSV includes old/new rank, paired survival gain, championship lift, Monte
Carlo standard error, conditional start rates, and original-owner starts/points.
Small differences relative to the reported standard error should be treated as
ties. This is an exploratory draft aid, not calibrated real-world win odds.

Scoring is half-PPR with six-point passing touchdowns and no first-down bonuses.
Kicker and defense scoring retains the FantasyPros baseline.

The September 3 Green Bay adjustment treats MarShawn Lloyd as the opening lead
back with a wide durability/role range. Josh Jacobs is unavailable while on the
Commissioner's Exempt List; his simulations use return points at Weeks 5, 9, 13,
or a full-season absence with probabilities of 15%, 25%, 35%, and 25%. The model
uses conditional IR occupancy, but platform eligibility for an exempt-list
player must be confirmed. These return probabilities are modeling assumptions,
not reported return dates. Lloyd's updated projection is split into lead/secondary
roles without double-discounting it for Jacobs' return. Kaleb Johnson and Chris
Brooks retain their previous scenario adjustments. This implementation carries
forward the September 3 news snapshot; it is not a fresh injury/news audit.

## Reproduction and limits

### Initial results (512 matched worlds)

| Player | Previous rank | New rank | Survival score gain | Monte Carlo SE |
| --- | ---: | ---: | ---: | ---: |
| Josh Allen | 10 | 23 | 1.414 | 0.274 |
| Brock Bowers | 20 | 25 | 1.377 | 0.226 |
| Lamar Jackson | 26 | 30 | 1.262 | 0.270 |
| Trey McBride | 19 | 33 | 1.125 | 0.235 |
| MarShawn Lloyd | 106 | 48 | 0.844 | 0.224 |
| Josh Jacobs | 170 | 174 | 0.049 | 0.103 |

These results do not substantiate a forced elite-QB/TE boost. Allen and McBride
start in 92.7% and 94.9% of available weeks on their surviving original teams,
but that persistence does not outweigh RB replacement scarcity in this policy.
Do not interpret the exact ordinal ranks as statistically distinct tiers.

A 512-world focused check with exempt-list IR disabled changes Jacobs' score
from 0.049 to -0.031 and his original-owner conditional start rate from 76.4%
to 11.6%, largely reflecting early drops. Neither score is meaningfully different
from zero at this sample size. A separate combined stress test with two waiver
rounds and no exempt IR yields Allen 1.693, McBride 1.271, Bowers 1.283, and
Jacobs -0.105. Those are score comparisons, not recalculated full-board ranks;
two assumptions change together in that stress test. The sensitivity checks are
additional to the 129,024 main paired counterfactuals.

### Running the model

The implementation is in `.artifact_work/survival_model.mjs` and the CSV builder
is `.artifact_work/build_chopped_rankings.mjs`. With the bundled Node runtime and
artifact-tool module junction, run the builder with
`--trials=512 --results=results_survival.json --simulate-only`, then `--export`.
Run tests with `node --test survival_model.test.mjs` from that directory.
Optional flags include `--seed=...`, `--waiver-rounds=2`, `--exempt-ir=false`,
and a comma-separated normalized-name `--focus=...` for simulation-only checks.

Position order for parameters is QB, RB, WR, TE, K, DST. Persistent lognormal
sigmas are 0.18/0.28/0.25/0.28/0.20/0.25; weekly coefficients of variation are
0.30/0.55/0.60/0.55/0.45/0.75. Injury-start probabilities per available week are
0.012/0.025/0.020/0.022/0.008/0, with one/three/six-week durations at
65%/25%/10%. These are transparent assumptions, not empirically calibrated fits.
Six-week spells are IR eligible. Individual injury risks, game correlations,
matchups, FAAB budgets, real draft behavior, and full current roster updates are
not modeled. Additional injury draws can lower totals already reflecting injury
risk in source projections. Positional depth arises from ownership and waivers,
but remains sensitive to these assumptions and the fixed draft universe.
