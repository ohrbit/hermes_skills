# Nano Banana Prompting

> **Get great images out of Google's Nano Banana (Gemini 3.1 Flash/Pro Image) models** — five official prompting frameworks, from text-to-image to multi-reference character consistency.

## Why this skill?

Most image prompts under-perform because they're vague or use negative framing ("no cars" instead of "empty street"). Google's own ultimate prompting guide distills what actually moves the needle on Nano Banana 2 / Pro. This skill puts those frameworks one command away so Hermes produces publication-grade images instead of random ones.

## What it does

- ✅ Model quick-reference (token limits, resolutions, reference-image counts, aspect ratios)
- ✅ 5 official prompting frameworks (text-to-image, multimodal w/ references, editing, style transfer, storyboards)
- ✅ Best-practice rules (specificity, positive framing, camera control, conversational iteration)
- ✅ Real worked examples copied from Google's guide
- 🔄 Covers NB2 advances: real-time web search, 4K upscaling, native ultra-wide ratios

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install nano-banana-prompting
```

## Quick Start

```text
In chat: "write a Nano Banana prompt for a cinematic fashion editorial, brown dress, cherry-red studio"
```

## How it works

Each framework is a fill-in formula. Example — Framework 1 (text-to-image, no references):

```
[Subject] <detailed subject with attributes>
[Action] <pose / movement>
[Location/context] <environment / atmosphere>
[Composition] <camera angle / framing>
[Style] <art style / medium / lighting>
```

Framework 2 (multimodal) lets you bind up to **14 reference images** for character consistency or product-environment merges:

```
Using the attached <ref1> as <role> and <ref2> as <role> [References],
<transform/combine/apply> <instruction> [Relationship].
Place it in <new environment> [New Scenario].
```

## Usage / Examples

### Basic
> "Generate a product shot of a ceramic mug on a oak table, morning light, 50mm, soft bokeh."

Hermes fills Framework 1 and emits the full NB prompt.

### Advanced
> "Keep this character's face (ref1) but put them in a cyberpunk alley (ref2 background)."

Hermes uses Framework 2 with both references for identity-locked scene swaps.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Frameworks, model table, best practices, examples |
| `references/` | Extended framework notes + edge cases |

## Related skills

- `comfyui` — if you'd rather generate via a node graph than the API
- `image_generate` (Hermes tool) — the actual image generation call

## Notes / caveats

- Nano Banana 2 = Gemini 3.1 Flash Image; Pro = Gemini 3 Pro Image. Know which you're calling.
- Reference images: up to 14 on both tiers.
- Knowledge cutoff Jan 2025 — pair with web search for current subjects.

## License

MIT — © 2024 ohrbit
