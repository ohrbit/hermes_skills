# hermes-voice-local

"Set up Hermes voice (STT + TTS) fully local and free — stop paying for OpenAI Whisper transcription and run faster-whisper inside the gateway venv. Load this whenever the user wants local/offline voice, reports losing money on voice→text, or STT/TTS silently fails."

## What it does
This skill is defined in [`SKILL.md`](./SKILL.md). Use it for: - "voice auf lokal", "local voice", "switch to local STT", "stop paying for transcription" - User reports money lost on voice→text - Voice messages fail to transcribe ("voice message could not be transcribed").

## Install
```bash
hermes skills install hermes-voice-local
```

## Contents
- `SKILL.md` — the skill definition (frontmatter + instructions)
- `references/` — deep-dive docs and code
- `templates/` — prompt / body templates
- `scripts/` — runnable helpers

## Category
`software-development`

---
*This README was generated from `SKILL.md` by scripts/generate_readmes.py.*
