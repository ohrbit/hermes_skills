#!/usr/bin/env bash
# setup_local_voice.sh — Hermes Voice → Local (free, offline)
# Performs Steps 0-5 of the hermes-voice-local skill:
#   - locate the gateway venv
#   - set stt.provider=local, tts.provider=edge
#   - install faster-whisper into the gateway venv
#   - free disk if needed (model download needs ~145 MB)
#   - verify local transcription works
# Step 6 (gateway restart) must be done MANUALLY by the user afterwards.
set -euo pipefail

echo "== Hermes Voice → Local setup =="

# --- Step 0: locate gateway venv ---
VENV=""
GW_PID=$(pgrep -f "hermes_cli.main gateway run" | head -1 || true)
if [ -n "$GW_PID" ]; then
  VENV=$(dirname "$(dirname "$(tr '\0' ' ' < /proc/$GW_PID/cmdline 2>/dev/null | awk '{print $1}')")")
fi
if [ -z "$VENV" ] || [ ! -x "$VENV/bin/python3" ]; then
  for cand in /usr/local/lib/hermes-agent/venv "$HOME/.hermes/venv" "$(python3 -c 'import hermes_cli,os;print(os.path.join(os.path.dirname(hermes_cli.__file__),"..","..","venv"))' 2>/dev/null || true)"; do
    if [ -x "$cand/bin/python3" ]; then VENV="$cand"; break; fi
  done
fi
if [ -z "$VENV" ]; then
  echo "ERROR: could not locate the Hermes gateway venv. Is Hermes installed?" >&2
  exit 1
fi
echo "gateway venv: $VENV"

# --- Step 2: switch providers ---
echo "== setting providers to local/free =="
hermes config set stt.provider local
hermes config set tts.provider edge || true

# --- Step 4: free disk if needed ---
FREE_MB=$(df -m / | awk 'NR==2 {print $4}')
echo "disk free: ${FREE_MB} MB"
if [ "${FREE_MB:-0}" -lt 300 ]; then
  echo "low disk — clearing safe caches..."
  rm -rf ~/.cache/ms-playwright ~/.cache/uv ~/.cache/pip ~/.cache/node-gyp
  rm -rf ~/.npm/_cacache
  apt-get clean 2>/dev/null || true
  rm -rf /var/lib/apt/lists/* 2>/dev/null || true
  journalctl --vacuum-size=30M 2>/dev/null || true
  echo "disk free now: $(df -m / | awk 'NR==2 {print $4}') MB"
fi

# --- Step 3: install faster-whisper into gateway venv ---
if "$VENV/bin/python3" -c "import faster_whisper" 2>/dev/null; then
  echo "faster-whisper already installed in venv"
else
  echo "== installing faster-whisper into gateway venv =="
  "$VENV/bin/pip" install faster-whisper
fi

# --- Step 5: verify local transcription ---
echo "== verifying local transcription (downloads base model on first run) =="
"$VENV/bin/python3" - <<'PY'
import glob, os
cache = os.path.expanduser('~/.hermes/cache/audio/*.ogg')
files = sorted(glob.glob(cache))
if not files:
    print("WARN: no cached voice messages found yet — model will download on first live use.")
    print("faster-whisper installed OK; skipping live transcription test.")
else:
    from faster_whisper import WhisperModel
    f = files[-1]
    print("file:", f, os.path.getsize(f), "bytes")
    m = WhisperModel("base", device="cpu", compute_type="int8")
    segs, info = m.transcribe(f)
    print("TRANSCRIBED:", repr(" ".join(s.text for s in segs)[:300]))
    print("lang:", info.language, "prob:", round(info.language_probability, 2))
PY

echo
echo "== DONE (steps 0-5). Now RESTART THE GATEWAY MANUALLY: =="
echo "   hermes gateway restart"
echo "   # or: systemctl --user restart hermes-gateway.service"
