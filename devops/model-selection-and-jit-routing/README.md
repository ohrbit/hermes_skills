# Model Selection & JIT Agent Routing

> **Pick the right model per task and route JIT agents to the best-fit provider** — balancing arena rank against *real* free-tier limits.

## Why this skill?

A high arena rank means nothing if the free tier gives you 5 requests/day. Gemini 3-Pro ranks top-10 but its free quota makes it useless as a fallback. This skill cross-checks live provider inventory + lmarena.ai ranks against verified free-tier caps, so you stop recommending traps and start routing parallel fan-outs to models that won't rate-limit them into the ground.

## What it does

- ✅ Task→model mapping (chat, coding, reasoning, vision, long-context)
- ✅ JIT agent-team routing: which provider per worker role
- ✅ Free-tier reality table (Nous / DeepSeek / Cerebras / NVIDIA / Gemini)
- ✅ Fallback chain wiring (with the `config set` string-bug fix)
- ✅ Live matrix refresh (`~/.hermes/data/model_matrix.json` + weekly cron)
- 🔄 Avoids NVIDIA/Cerebras as parallel-fan-out defaults (shared caps drain fast)

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install model-selection-and-jit-routing
```

## Quick Start

```bash
# read the live matrix first
python3 ~/.hermes/scripts/refresh_model_matrix.py --report
# then ask: "which model for a wide JIT fan-out?"
# → tencent/hy3:free (nous, unlimited) is the safe default
```

## How it works

```
task volume / latency / parallelism
   │
   ▼
filter providers by REAL free-tier limit (not rank)
   │
   ▼
rank survivors by lmarena overall / sub-rank
   │
   ▼
apply size-vs-rank caveat (knowledge/long-context → bigger model)
```

Known-good fallback chain: `tencent/hy3:free` → `deepseek-v4-pro` → `deepseek-ai/deepseek-v4-flash`.

## Usage / Examples

### Basic
> "What model should the merge-reviewer worker use?"

Heavy single worker → `deepseek-v4-pro`. Wide parallel fan-out → `tencent/hy3:free` (Nous unlimited).

### Advanced
Wiring fallback via YAML (the `config set` string bug):
```python
import yaml; p='/root/.hermes/config.yaml'; d=yaml.safe_load(open(p))
d['fallback_providers']=[{'provider':'deepseek','model':'deepseek-v4-pro'},
                         {'provider':'nvidia','model':'deepseek-ai/deepseek-v4-flash'}]
yaml.safe_dump(d,open(p,'w'),sort_keys=False,allow_unicode=True)
```

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Routing logic, free-tier table, pitfalls |
| `references/free-tier-limits.md` | Sources + detail per provider |
| `scripts/refresh_model_matrix.py` | Provider inventory refresh |

## Related skills

- `jit-agent-teams` — the teams you route models onto
- `agent-swarm-loop` — workers get models from this skill

## Notes / caveats

- **Rank ≠ usability** — always cross-check arena rank against the real free limit.
- Nous `:free` is the ONLY true sustained free tier; never hardcode the inventory (it rotates).
- lmarena raw API is Cloudflare-blocked — only `web_extract` on the rendered page works.

## License

MIT — © 2024 ohrbit
