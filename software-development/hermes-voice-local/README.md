# Hermes Voice → Local (free, offline)

> **Make Hermes transcribe your voice locally and speak via free Edge TTS** — stop paying OpenAI per voice message.

## Why this skill?

The silent money leak is almost always `stt.provider: openai` → paid `whisper-1` billed on every voice message. This skill flips Hermes to fully local STT (faster-whisper, inside the gateway venv) + free Edge TTS, with zero per-message cost. It also covers the failure mode where voice messages "could not be transcribed" because the provider is misconfigured.

## What it does

- ✅ Switch STT to local faster-whisper (free)
- ✅ Switch TTS to Edge (free)
- ✅ Locate the gateway venv dynamically (STT runs there, not system python)
- ✅ Diagnose what's currently paid (parse config.yaml directly)
- ✅ Step-by-step free end state
- 🔄 Works on linux + macos

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install hermes-voice-local
```

## Quick Start

```bash
hermes config set stt.provider local
hermes config set tts.provider edge
# verify
python3 -c "import yaml;c=yaml.safe_load(open('/root/.hermes/config.yaml'));print(c.get('stt'),c.get('tts'))"
```

## How it works

```
voice message → gateway venv (faster-whisper, local) → transcript → Hermes
Hermes reply → Edge TTS (free) → voice bubble
```

The correct free end state: `stt.provider=local`, `tts.provider=edge`, `terminal.backend=local`, `model.provider=nous`.

## Usage / Examples

### Basic
> "Stop paying for voice transcription."

Runs Step 0–2: locate gateway venv, diagnose current paid provider, switch to local + edge.

### Advanced
Gateway not running? The skill has fallback venv paths (`hermes_cli` package location, `/usr/local/lib/hermes-agent/venv`).

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Steps, diagnosis, pitfalls |
| `references/` | Extended setup notes |

## Related skills

- Your `config.yaml` — the file this edits
- `hermes-context-stack` — for safe config management

## Notes / caveats

- **No `hermes config get`** — parse `config.yaml` with yaml directly.
- STT runs inside the **gateway venv**, not your system `python3` — install faster-whisper there.
- The leak is `stt.provider: openai` → paid `whisper-1`; flip to `local`.

## License

MIT — © 2024 ohrbit (author: ohrbit)
