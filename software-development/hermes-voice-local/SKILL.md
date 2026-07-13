---
name: hermes-voice-local
description: "Set up Hermes voice (STT + TTS) fully local and free — stop paying for OpenAI Whisper transcription and run faster-whisper inside the gateway venv. Load this whenever the user wants local/offline voice, reports losing money on voice→text, or STT/TTS silently fails."
version: 1.1.0
author: ohrbit
license: MIT
platforms: [linux, macos]
tags: [hermes, voice, stt, tts, whisper, local, cost, setup, free]
---

# Hermes Voice → Local (free, offline)

Make Hermes transcribe your voice messages **locally** (no OpenAI charges) and speak
back via the free Edge TTS voice. This is the correct, cost-free voice setup.

## When to use
- "voice auf lokal", "local voice", "switch to local STT", "stop paying for transcription"
- User reports money lost on voice→text
- Voice messages fail to transcribe ("voice message could not be transcribed")

## TL;DR — the correct end state
| Setting | Value | Cost |
|---------|-------|------|
| `stt.provider` | `local` (faster-whisper) | 🆓 |
| `tts.provider` | `edge` | 🆓 |
| `terminal.backend` | `local` | 🆓 |
| `model.provider` | `nous` (or any non-paid) | 🆓 |

The leak is almost always `stt.provider: openai` → paid `whisper-1` per voice message.

## Step 0 — Locate the Hermes gateway venv (do NOT guess)
STT runs inside the gateway's Python, not your system `python3`. Find it dynamically:
```bash
GW=$(pgrep -af "hermes_cli.main gateway run" | head -1 | awk '{print $1}')
VENV=$(dirname "$(dirname "$GW")")
echo "gateway venv: $VENV"
# Fallbacks if gateway isn't running:
[ -z "$VENV" ] && VENV=$(python3 -c "import hermes_cli,os;print(os.path.join(os.path.dirname(hermes_cli.__file__),'..','..','venv'))" 2>/dev/null)
[ -z "$VENV" ] && VENV=/usr/local/lib/hermes-agent/venv
```

## Step 1 — Diagnose what's currently paid
```bash
python3 -c "
import yaml
c = yaml.safe_load(open(os.path.expanduser('~/.hermes/config.yaml')))
print('stt.provider =', c.get('stt',{}).get('provider'))
print('tts.provider =', c.get('tts',{}).get('provider'))
"
```
Note: there is **no** `hermes config get` command — parse the yaml directly.

## Step 2 — Switch providers (free)
```bash
hermes config set stt.provider local
hermes config set tts.provider edge   # only if not already
```

## Step 3 — Install faster-whisper into the GATEWAY venv
**PITFALL:** installing into system `python3` (e.g. `pip install --break-system-packages`)
does NOT help — the gateway won't see it.
```bash
"$VENV/bin/pip" install faster-whisper
"$VENV/bin/python3" -c "import faster_whisper; print('ok', faster_whisper.__version__)"
```

## Step 4 — Verify local transcription works
```bash
"$VENV/bin/python3" - <<'PY'
import glob, os
from faster_whisper import WhisperModel
f = sorted(glob.glob(os.path.expanduser('~/.hermes/cache/audio/*.ogg')))[-1]
print("file:", f, os.path.getsize(f), "bytes")
m = WhisperModel("base", device="cpu", compute_type="int8")
segs, info = m.transcribe(f)
print("TRANSCRIBED:", repr(" ".join(s.text for s in segs)[:300]))
print("lang:", info.language, "prob:", round(info.language_probability, 2))
PY
```
First run downloads the model (~145 MB) — ensure enough free disk for it. Real text = success.

## Step 6 — Restart the gateway (USER action, not the agent)
The gateway is a systemd-managed service and the agent's own shell is a child of it,
so the agent **cannot** restart it (a safety guard blocks this to prevent killing its
own session). Run this in a shell **outside the chat**:
```bash
hermes gateway restart
# or, if systemd-managed:
systemctl --user restart hermes-gateway.service
```

## Step 7 — Confirm it's live
```bash
ps aux | grep "hermes_cli.main gateway run" | grep -v grep   # check START TIME
python3 -c "import yaml;c=yaml.safe_load(open(os.path.expanduser('~/.hermes/config.yaml')));print(c['stt']['provider'])"
```
Then send a voice message — it should transcribe with **$0** cost.

## Bonus: real Telegram voice notes (not file attachments)
Hermes' `text_to_speech` returns `.mp3`. Telegram only shows a **voice bubble** for
`.ogg`/Opus. Convert for true voice notes:
```bash
ffmpeg -i reply.mp3 -c:a libopus -b:a 32k reply.ogg
```

## Verification checklist
- [ ] `stt.provider = local`, `tts.provider = edge`
- [ ] faster-whisper importable in the **gateway venv**
- [ ] Local transcription of a cached `.ogg` returns real text
- [ ] Gateway restarted by the user, new start time confirmed
- [ ] Live voice message transcribes, no charges

## Pitfalls summary
1. **Wrong venv** — install faster-whisper in the gateway venv, not system python.
2. **Model download needs disk** — the `base` whisper model is ~145 MB; ensure free space.
3. **Restart blocked** — agent cannot restart its own gateway; user does it manually.
4. **No `hermes config get`** — parse the yaml directly.

## Automated setup
A ready-to-run script that performs Steps 0–5 is included at
`scripts/setup_local_voice.sh`. Run it, then do the manual gateway restart (Step 6).
