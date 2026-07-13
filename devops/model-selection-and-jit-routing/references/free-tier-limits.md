# Free-Tier Limits — Real Conditions (verified July 2026)

Researched because arena.ai rank ≠ practical usability. A top-ranked model behind
a 5-requests/day free cap is useless as a default/fallback. Re-verify periodically;
providers change these quietly (Gemini Flash was cut from 250→20 RPD in one instance).

## Nous Portal (`:free` suffix)
- **Unlimited** free usage — the only true sustained free tier here.
- Inventory rotates; ~278 total models but only `:free`-suffixed are free. Paid frontier
  (claude/gpt/gemini) are listed but NOT free — never recommend as free.
- Best free model: `tencent/hy3:free` (arena text ~#110). Daily driver.

## Gemini (Google AI Studio) — free tier
- **Frontier models nearly unusable free:** gemini-3-pro ≈ **5 RPD**, gemini-3-flash ≈ 5 RPD
  observed; Flash historically 20–250 RPD and has been slashed without notice.
- Limits are now shown per-project in AI Studio dashboard, not in public docs.
- Free tier has NO spend-based limit (N/A); Tier 1 needs a linked billing account.
- Dimensions: RPM, TPM (input), RPD. RPD resets midnight Pacific. Limits are per-PROJECT, not per-key.
- **Verdict:** use only for rare hard-reasoning one-shots. NOT for fallback or JIT default.
- Key format: `AIza*` (legacy) or `AQ.*` (newer). Auth: `?key=` or `x-goog-api-key` header, NOT Bearer.
- Source: ai.google.dev/gemini-api/docs/rate-limits, docs/pricing (2026-07-03).

## Cerebras — free tier
- **1,000,000 tokens/day** (input+output combined), **30 RPM**, no credit card.
- Very fast (wafer-scale, up to ~2000 tok/s). Great for latency-sensitive single bursts.
- Shared daily cap drains fast under parallel/long work → bad JIT fan-out default.
- Models seen: gpt-oss-120b, gemma-4-31b (arena ~#49), zai-glm-4.7 (~#64).
- Source: getaiperks.com/cerebras-free-tier-guide, inference-docs.cerebras.ai/support/rate-limits.

## NVIDIA NIM (build.nvidia.com) — free tier
- **1,000 inference credits on signup** (up to 5,000 on request) + **40 RPM**. No card.
- Credits are FINITE (not just a rate) → unsuitable for wide/repeated JIT fan-out.
- Rate-limit increases are NOT granted on request for free tier.
- Large catalog (~121 models): deepseek-v4-pro/flash, minimax-m3, nemotron-3-ultra-550b, etc.
- Source: decodethefuture.org/nvidia-nim-api-explained, forums.developer.nvidia.com.

## DeepSeek — free/paid
- **5M tokens free to start**, then pay-as-you-go (cheap). No RPD cliff → reliable.
- Off-peak discount 16:30–00:30 UTC (historically −50–75% on V3/R1; V4 off-peak TBD).
- Models: deepseek-v4-pro (arena ~#42), deepseek-v4-flash (~#70).
- **Best reliable non-free** option: no rate-limit surprises, near-free cost.
- Source: api-docs.deepseek.com/quick_start/pricing, nxcode.io deepseek-api-pricing-2026.

## Practical routing conclusion
- Sustained / parallel / JIT fan-out → `hy3:free` (nous, unlimited) only.
- Reliable heavy single worker → `deepseek-v4-pro` (paid-cheap, no cliff).
- Latency burst, one at a time → `gemma-4-31b` (cerebras, within 1M/day).
- Occasional / eval → NVIDIA (mind finite credits).
- Rare premium reasoning shot → gemini-3.1-pro (≈5/day — hand-triggered only).
