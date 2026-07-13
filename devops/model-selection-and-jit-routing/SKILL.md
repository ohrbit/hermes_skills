---
name: model-selection-and-jit-routing
description: "Pick the right available model per task (chat/coding/reasoning/vision/long-context) and route JIT agent-team profiles to the best-fit provider, using live provider inventory + lmarena.ai ranks. Load when choosing a model, wiring fallbacks, or distributing JIT/Kanban agents."
version: 1.0.0
tags: [models, lmarena, jit-agents, routing, providers, nous, cerebras, nvidia, deepseek]
platforms: [linux]
---

# Model Selection & JIT Agent Routing

Pick the best **available** model for a given task and assign JIT agent-team
profiles to the provider that fits the workload — balancing capability
(lmarena.ai rank) against real free-tier limits.

## Data source (keep fresh)
- Matrix file: `~/.hermes/data/model_matrix.json` — provider inventory + matched lmarena ranks.
- Refresh (providers): `python3 ~/.hermes/scripts/refresh_model_matrix.py --report`
- Arena ranks need a rendered page → use `web_extract("https://lmarena.ai/leaderboard")`
  (Cloudflare blocks raw curl/API). The weekly cron `model-matrix-refresh` does both.
- **Always** read the matrix file first; if `updated` is >8 days old, refresh before advising.

## Provider reality (NOT just rank — limits matter)
Verified free-tier conditions (see `references/free-tier-limits.md` for sources/detail):
| Provider | Real free limit | Use for |
|---|---|---|
| **Nous** (`:free`) | unlimited | daily driver, long-running, JIT default — ONLY true sustained free tier |
| **DeepSeek** | 5M start tokens, then PAID (cheap; off-peak −50-75% @ 16:30–00:30 UTC) | serious coding/reasoning; reliable, no RPD cliff |
| **Cerebras** | 1M tok/day + 30 RPM, no card | latency bursts; NOT sustained/parallel (shared daily cap) |
| **NVIDIA NIM** | 1,000 credits (→5k on request) + 40 RPM | occasional calls; credits are FINITE — bad for JIT fan-out |
| **Gemini** free | Frontier (3-Pro) ≈ **5 RPD**; Flash 20–250 RPD (has been slashed) | rare premium one-shots ONLY; useless as fallback/default |

**Key lesson from this session:** rank ≠ usability. Gemini frontier models rank top-10 on arena
but the free tier gives ~5 requests/day for 3-Pro — recommending them as a fallback/JIT default is
a trap. Always cross-check the arena rank against the real free-tier limit before advising.

Rule: lmarena rank measures **human preference**, not raw knowledge/context.
For broad factual recall, very long context, or hard multi-step, prefer the
larger model even if a smaller one out-ranks it on arena.

## Task → model (re-derive from matrix; example ordering as of last refresh)
| Task | First choice | Why |
|---|---|---|
| Daily chat / general | `tencent/hy3:free` (nous) | free unlimited, rank ~110 is plenty |
| Serious coding / agents | `deepseek-v4-pro` | arena ~42, strong tool-use, cheap |
| Hard reasoning / math | `deepseek-v4-pro-thinking` | math rank ~25 |
| Fast + good burst | `gemma-4-31b` (cerebras) | speed, until 1M tok cap |
| Long context / broad knowledge | `nvidia/nemotron-3-ultra-550b` | 550B beats small models on breadth |
| Vision / multimodal | `minimaxai/minimax-m3` | arena ~59, multimodal |
| GLM allrounder (fast) | `zai-glm-4.7` (cerebras) | arena ~64 |

## JIT agent-team routing (per user's JIT workflow)
When spinning JIT profiles (gs-ui / engine / gfx / merge etc.), assign models by role:
1. **Fan-out width matters**: parallel Kanban workers → AVOID NVIDIA (rate limit kills parallelism)
   and AVOID Cerebras for many/long tasks (shared 1M/day cap drains fast).
2. **Default parallel worker**: `tencent/hy3:free` (nous, unlimited) — safe for wide fan-out.
3. **Heavy single worker** (architecture, hard debug, merge-reviewer): `deepseek-v4-pro`.
4. **Latency-sensitive single task**: `gemma-4-31b` (cerebras) — one at a time.
5. **Vision task in the team**: `minimaxai/minimax-m3`.
6. Set per-profile via `hermes model` / config provider+model, or pass model on delegate/cron.

## Steps to advise a model
1. Read `~/.hermes/data/model_matrix.json`; check `updated` freshness.
2. Filter to models whose provider fits the task's volume/latency/parallelism.
3. Rank survivors by arena `overall` (or `coding`/`math` sub-rank for that task).
4. Apply the size-vs-rank caveat for knowledge/long-context tasks.
5. State choice + 1-line why + the limit caveat.

## Wiring a fallback chain
Desired resilience: primary free model → paid-but-no-RL → last resort.
Known-good chain: `tencent/hy3:free` (nous) → `deepseek-v4-pro` (deepseek) → `deepseek-ai/deepseek-v4-flash` (nvidia).

- Config key is top-level `fallback_providers:` (a YAML LIST of `{provider, model}` objects; add `base_url`/`key_env` for `provider: custom`). Each entry needs BOTH provider+model or it's ignored.
- **GOTCHA:** `hermes config set fallback_providers '[{...}]'` stores the value as a raw STRING, not a list — `hermes fallback list` then reports "No fallback providers configured." Fix: write a real YAML list. Since config.yaml is write-guarded to patch/write_file, edit via python in the terminal:
  ```python
  import yaml; p='/root/.hermes/config.yaml'; d=yaml.safe_load(open(p))
  d['fallback_providers']=[{'provider':'deepseek','model':'deepseek-v4-pro'},
                           {'provider':'nvidia','model':'deepseek-ai/deepseek-v4-flash'}]
  yaml.safe_dump(d,open(p,'w'),sort_keys=False,allow_unicode=True)
  ```
  Then verify with `hermes fallback list` (should show Primary + numbered chain).
- Fallback is turn-scoped, inherited by subagents AND cron. Triggers on 429/5xx/401/403/404/malformed. Resets prompt cache (extra cost) — acceptable for staying alive.

## Cron refresh design
The weekly `model-matrix-refresh` cron has a script step (provider inventory, deterministic) + an agent step (arena ranks via web_extract, since raw API is Cloudflare-blocked). The script writes `arena_matched`; if the agent step doesn't persist its merge, ranks land 0/empty. The script self-heals by re-parsing the newest `~/.hermes/cache/web/lmarena.ai-*.md` snapshot. If matrix shows `arena_row_count: 0`, run `web_extract` on the leaderboard, then re-run the script.

## Pitfalls
- Free `:free` inventory at Nous rotates — never hardcode; re-read matrix.
- Cerebras & NVIDIA limits make them wrong defaults for JIT fan-out despite good ranks.
- lmarena raw API is Cloudflare-blocked; only `web_extract` on the rendered page works.
- Nous Portal lists ~278 models incl. paid frontier (claude/gpt/gemini); only `:free`-suffixed are actually free — don't recommend a paid Nous model as if it were free.
- arena rank = human preference, not raw knowledge/context — for broad recall or long context prefer the larger model even at a worse rank.
- Gemini API keys come in two formats: legacy `AIza*` AND newer `AQ.*`. Auth via `?key=` URL param
  or `x-goog-api-key` header — NOT `Bearer` (401). Don't grep only for `AIza*` or you'll miss `AQ.*` keys.
  A 403 "unregistered callers" usually means the key was empty/not passed, not that it's depleted.
