---
name: nano-banana-prompting
description: "Prompting frameworks and patterns for Google Nano Banana (Gemini 3.1 Flash/Pro Image) models. Covers 5 core frameworks from Google's official guide."
category: creative
tags: [prompting, nano-banana, gemini, image-generation, google-ai]
version: 1.1.0
---

# Nano Banana Prompting Skill

**Source:** [Google Cloud Blog — Ultimate Prompting Guide for Nano Banana](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana?hl=en)  
**Authors:** Khulan Davaajav & Hussain Chinoy | **Date:** March 5, 2026  
**Models:** Nano Banana 2 (Gemini 3.1 Flash Image) / Nano Banana Pro (Gemini 3 Pro Image)

---

## Model Quick Reference

| Capability | Nano Banana 2 | Nano Banana Pro |
|------------|---------------|-----------------|
| Max Input Tokens | 131,072 | 65,536 |
| Max Output Tokens | 32,768 | 32,768 |
| Resolutions | 0.5K, 1K, 2K, 4K | 1K, 2K, 4K |
| Aspect Ratios | 16 standard + 1:4, 4:1, 1:8, 8:1 ultra-wide | 16 standard |
| Reference Images | Up to 14 | Up to 14 |
| Real-time Web Search | ✅ | ✅ |
| Knowledge Cutoff | Jan 2025 | Jan 2025 |

**Key Advances (NB2):** Real-time web search, text rendering, translations, 4K upscaling, cohesive narratives/storyboards, native ultra-wide aspect ratios.

---

## Best Practices (Universal)

1. **Be specific** — Concrete details on subject, lighting, composition
2. **Use positive framing** — Describe what you *want* ("empty street" not "no cars")
3. **Control the camera** — Photographic/cinematic terms: "low angle", "aerial view", "dolly zoom"
4. **Iterate conversationally** — Refine with follow-up prompts
5. **Start with a strong verb** — Tells model the primary operation: `generate`, `edit`, `transform`, `render`

---

## Five Prompting Frameworks (Official Guide)

---

### Framework 1: Image Generation — Text-to-Image (No References)

**Formula:** `[Subject] + [Action] + [Location/Context] + [Composition] + [Style]`

**Template:**
```
[Subject] <detailed subject description with attributes>
[Action] <what the subject is doing, pose, movement>
[Location/context] <environment, background, atmosphere>
[Composition] <camera angle, framing, shot type>
[Style] <art style, medium, lighting, technical specs>
```

**Example (from guide):**
```
[Subject] A striking fashion model wearing a tailored brown dress, sleek boots, and holding a structured handbag.
[Action] Posing with a confident, statuesque stance, slightly turned.
[Location/context] A seamless, deep cherry red studio backdrop.
[Composition] Medium-full shot, center-framed.
[Style] Fashion magazine style editorial, shot on medium-format analog film, pronounced grain, high saturation, cinematic lighting effect.
```

---

### Framework 2: Image Generation — Multimodal Generation (With References)

**Formula:** `[Reference Images] + [Relationship Instruction] + [New Scenario]`

**Template:**
```
Using the attached <ref1 description> as <role> and the attached <ref2 description> as <role> [References],
<transform/combine/apply> <instruction> [Relationship].
Place it in <new environment/context> [New Scenario].
```

**Example (from guide):**
```
Using the attached napkin sketch as the structure and the attached fabric sample as the texture [References],
transform this into a high-fidelity 3D armchair render [Relationship].
Place it in a sun-drenched, minimalist living room [New Scenario].
```

**Pro Tip:** Combine up to 14 reference images for character consistency, product-environment merging, or style transfer chains.

---

### Framework 3: Image Editing — Conversational Editing (No New References)

**Operations:** Semantic masking (inpainting), object removal, attribute modification, lighting changes

**Principle:** Be explicit about what stays unchanged

**Examples:**
```
"Remove the man from the photo"
"Change the dress color from red to emerald green, keep everything else identical"
"Make the lighting golden hour instead of midday"
"Add a subtle smile to the subject's face"
```

---

### Framework 4: Image Editing — Composition & Style Transfer (With New References)

| Operation | Approach | Example |
|-----------|----------|---------|
| **Adding elements** | Upload base image + object image → instruct combination | "Place the uploaded watch on the model's left wrist, match lighting" |
| **Style transfer** | Upload photo → request recreation in target style | "Recreate this portrait as a Van Gogh-style painting, keep facial features recognizable" |
| **Environment swap** | Upload subject + new background → blend | "Place the product on the uploaded marble countertop, match shadows" |
| **Character consistency** | Upload character refs + new pose/scene → maintain identity | "Put this character in a cyberpunk alley, same outfit and facial features" |

---

### Framework 5: Real-Time Information from Web Search

**How it works:** Model actively searches web → retrieves real-world data → visualizes per instructions

**Formula:** `[Source/Search Request] + [Analytical Task] + [Visual Translation]`

**Template:**
```
[Search for <specific real-time data: weather, news, stock price, event, location data>]
+ [Analytically, use this data to <modify/adapt/determine> the scene: <specific logic>]
+ [Visualize this in <creative concept/format>: <detailed visual description>]
```

**Example (from guide):**
```
[Search for current weather and date in San Francisco]
+ [Analytically, use this data to modify the scene (e.g., if raining, make it look grey and rainy)]
+ [Visualize this in a miniature city-in-a-cup concept embedded within a realistic, modern smartphone UI]
```

**Use Cases:**
- Live weather → atmospheric scene generation
- Stock/crypto prices → data visualization art
- Breaking news → editorial illustrations
- Sports scores → dynamic scoreboard graphics
- Local events → promotional posters

---

## Aspect Ratio Cheatsheet (Nano Banana 2)

| Ratio | Use Case |
|-------|----------|
| 1:1 | Social posts, avatars, icons |
| 16:9 | YouTube thumbnails, widescreen |
| 9:16 | Stories, Reels, TikTok |
| 4:3 / 3:4 | Photos, presentations |
| 21:9 | Cinematic, ultrawide monitors |
| **1:4 / 4:1** | **Banners, panoramas, comic strips** |
| **1:8 / 8:1** | **Extreme panoramas, timelines, film strips** |

*NB Pro lacks the ultra-wide ratios (1:4, 4:1, 1:8, 8:1)*

---

## Resolution Guidance

| Resolution | Pixels | Best For |
|------------|--------|----------|
| 0.5K | ~512px | Quick drafts, thumbnails |
| 1K | ~1024px | Web, social media |
| 2K | ~2048px | Print, high-quality web |
| 4K | ~4096px | Large format, detailed art |

---

## Reference Image Best Practices

- **Max 14 images** per prompt (PNG, JPEG, WebP, HEIC, HEIF)
- **Consistent lighting** across refs = better blending
- **High contrast** subjects separate cleanly
- **Transparent backgrounds** (where possible) for object insertion
- **Multiple angles** of same subject → 3D consistency

---

## Prompting Anti-Patterns (What to Avoid)

| ❌ Avoid | ✅ Prefer |
|----------|-----------|
| "Make it pop" | "Increase saturation by 20%, add rim light" |
| "No cars" | "Empty street, pedestrian only" |
| "Cool style" | "Cyberpunk neon aesthetic, rain-slick streets" |
| "Fix the face" | "Symmetrical facial features, natural skin texture" |
| Vague iterations | "Change X to Y, keep Z unchanged" |

---

## Quick Reference Cards

### Text-to-Image Card
```
VERB: generate / render / create
SUBJECT: [who/what + details]
ACTION: [pose/motion/interaction]
CONTEXT: [where + atmosphere]
COMPOSITION: [angle + framing + lens]
STYLE: [medium + lighting + color palette + technical]
ASPECT: [ratio] | RESOLUTION: [0.5K/1K/2K/4K]
```

### Multimodal Card
```
VERB: transform / combine / adapt / merge
REFS: [img1=role, img2=role, ...]
RELATIONSHIP: [how refs map to output]
SCENARIO: [new environment/context]
STYLE: [target aesthetic]
```

### Web Search Card
```
VERB: visualize / illustrate / depict
SEARCH: [specific query for live data]
LOGIC: [if X then Y analytical rule]
CONCEPT: [creative visual metaphor]
STYLE: [presentation format]
```

---

## Integration with Hermes

### Current Hermes Image Generation
- **Tool:** `image_generate` (uses FAL/Flux via Nous subscription)
- **Not:** Native Nano Banana access — requires Google Cloud/Vertex AI project with billing

### To Use Nano Banana via Hermes:
1. **Option A:** Add Google API key (`hermes setup` → Google Gemini)
2. **Option B:** Create custom skill wrapping Vertex AI REST API
3. **Option C:** Use Google AI Studio web UI for prompting, save results

### Suggested Workflow
```
1. Use this skill's frameworks to craft prompts
2. Test in Google AI Studio (free tier)
3. Save successful prompts as templates in this skill
4. Batch generate via custom script if API access obtained
```

---

## Skill Maintenance

- **Update when:** Google releases new Nano Banana features/model versions
- **Test frameworks** against actual model outputs when API access available
- **Add templates** for recurring use cases (product mockups, character sheets, etc.)

---

## References

- [Google Cloud Blog — Ultimate Prompting Guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana?hl=en)
- [Gemini 3.1 Flash Image Docs](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-1-flash-image)
- [Gemini 3 Pro Image Docs](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image)
- [C2PA Content Credentials](https://c2pa.org/)
- [SynthID Watermarking](https://deepmind.google/technologies/synthid/)