# Evaluated Repos — 2026-07-10

## davidondrej/skills
- **Type:** Prompt-only collection
- **Categories:** agent-orchestration, skill-authoring, research-and-web, thinking-and-docs, ops-and-setup
- **Verdict:** Adapt later. Contains generic agent workflow prompts but no executable code. If importing, prioritize `ops-and-setup` and `skill-authoring`; ignore `research-and-web` for this user's stack.
- **Notes:** 2.1k stars, actively maintained. Good reference for prompt structure, but not directly usable in Hermes without adaptation.

## ohrbit/riftagent
- **Type:** Prompt-orchestration demo
- **Core:** LLM-driven gacha item generation → image prompt → studio-quality product shot
- **Verdict:** Skip for import. Strong viral hook for X/Twitter, but it's a concept demo with `.md` specs only. No tested workflow, no executable code, image backend is vendor-locked to Nano Banana by default.
- **Session context:** User posted about it on X; the idea travels well socially. If the user wants the *pattern* (theme → tier roll → item description → image prompt), that can be adapted, but the repo itself is not a production-ready skill.
- **Notes:** 0 stars, 1 contributor, 4 commits. MIT licensed.

## google-ai-edge/gallery
- **Type:** App-coupled skill repo
- **Platform:** Android/iOS/macOS app using LiteRT, Gemma 4, FunctionGemma 270m
- **Skills found:** `skills/built-in/` (calculate-hash, interactive-map, kitchen-adventure, mood-tracker, qr-code, query-wikipedia, send-email, text-spinner) and `skills/featured/` (mood-music, restaurant-roulette, virtual-piano)
- **Verdict:** Skip for direct import. Skills are tightly coupled to the mobile Gallery app's runtime. Not usable on Hetzner without unwinding from the LiteRT/Gallery host.
- **Possible exception:** `query-wikipedia` is conceptually portable, but requires rewriting the tool-calling layer for Hermes.
- **Notes:** 24k stars, Google-backed, actively maintained. The MCP/ folder may contain integration hints worth a look if the user wants deeper exploration.
