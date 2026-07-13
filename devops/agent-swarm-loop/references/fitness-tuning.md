# Fitness-tuning reference — the binary-cliff trap (learned from Tunnel Derby)

When a swarm's fitness metric is survival % (or any pass/fail-style metric) and
you tune a continuous parameter expecting a smooth gradient (e.g. 0% → 40% →
100%), you will very often hit a **BINARY CLIFF** instead: the metric jumps from
0% to 100% across a tiny parameter window with NO intermediate band. This makes
the GA unable to *select* (nothing to rank between 0% and 100%).

## What happened (Tunnel Derby, R1–R4)
4 rounds, each fitness-gated, each rejected, each taught the next round:

| Round | Change | Survival | Diagnosis |
|-------|--------|----------|-----------|
| R1 | CURVE_FORCE=240 | 0% | lateral force too strong → all crash at s≈504 |
| R2 | tunnel minR 14 | 0% | tunnel structurally impassable (ship r=7, <7 clearance) → all crash s=240 |
| R3 | minR 35, CF=30 | 100% | tunnel too easy → no selection pressure (gain=0) |
| R4 | sweep | 0%/100% | **binary cliff**: CF=35→100%, CF=40→0%; centering 1.3x→0%, 1.5x→100% |

Root cause of the cliff: the entity either *stays centered* (survives) or *flies
off at the first sharp bend* (dies). No smooth middle. A GA needs a gradient.

## The Orchestrator-sweep methodology (do this BEFORE re-dispatching workers)
Don't blind-rerun agents on a hunch. Once you have the modules assembled, the
Orchestrator runs a **local parameter sweep** in Node/Python to find the cliff
and the true passable window:

```js
// pattern: for each candidate constant, run the GA harness, print survival %
for (const CF of [12,30,50,100,200]) { ... run 40-gen POP=20 ... print survival }
// find the transition point, then sweep finely around it
for (const CF of [35,40,50,60,70]) { ... }
```
This took seconds locally vs. 5+ minutes per Modal worker round, and revealed the
cliff in R3/R4 that 4 worker rounds never found.

## How to get a real gradient (design fixes, not tuning)
1. **Look-ahead steering** — the agent pre-computes the NEXT curvature and steers
   proactively, so a high-skill genome beats a low-skill one *gradually* (small
   error tolerated, large error crashes). Without look-ahead the cliff persists.
2. **Soft failure** — clamp the failing variable AND zero its velocity on contact
   (a bounce), so bad actors lose *speed/reach* rather than instantly dying. This
   spreads outcomes across a range instead of 0/100.
3. **Softer environment** — reduce curvature/sharpness so middling skill survives;
   then sharpen only until survival lands in the 40–70% band.
4. **Continuous fitness** — prefer a metric that is inherently graded (e.g. mean
   reach distance, mean survival time) over binary pass/fail. A continuous metric
   almost always has a gradient even when the binary one cliffs.

## Verification rule
A round that reports "survival 100%" or "survival 0%" from a worker's self-test is
NOT validated. The Orchestrator must run the harness itself (assemble the real
branches, run the GA) and confirm the metric is in the target band with positive
convergence gain. Worker self-reports lie / are on a different tunnel.
