#!/usr/bin/env bash
# hdd_cleanup.sh — safe nightly disk cleanup + Hermes self-update + lean GitHub backup
#               + post-update cleanup + service restart (with health check + agent guard).
# Order: cleanup -> update -> LEAN BACKUP TO GITHUB -> cleanup-again -> restart (+healthcheck)
# Scope (verified safe during manual cleanup session):
#   - hermes rotated/active logs
#   - JIT profile archives, hermes skills index cache, npx caches
# NEVER touches: state.db, whisper model cache, runtimes, obsidian-vault, /root project dirs.
set -u

LOG="/root/.hermes/cron/output/hdd_cleanup.log"
mkdir -p "$(dirname "$LOG")"

BACKUP_REPO="ohrbit/hermes_backups"
BACKUP_BRANCH="main"
BACKUP_FILE="backup.tar.gz"
TOKEN=$(grep '^GITHUB_TOKEN=' /root/.hermes/.env | cut -d= -f2-)

echo "=== Nightly maintenance $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG"

BEFORE=$(df -h / | awk 'NR==2{print $5" used="$3" avail="$4}')

cleanup_stage() {
  echo "--- cleanup pass ---" | tee -a "$LOG"
  rm -f /root/.hermes/logs/agent.log.1 /root/.hermes/logs/agent.log.2 /root/.hermes/logs/agent.log.3 \
        /root/.hermes/logs/errors.log.1 /root/.hermes/logs/errors.log.2 \
        /root/.hermes/logs/gateway-exit-diag.log 2>/dev/null
  for f in /root/.hermes/logs/agent.log /root/.hermes/logs/errors.log /root/.hermes/logs/gateway.log; do
    [ -f "$f" ] && : > "$f"
  done
  [ -f /var/log/fail2ban.log ] && : > /var/log/fail2ban.log
  rm -f /root/.hermes/profiles-archive/*.tar.gz 2>/dev/null
  rm -rf /root/.hermes/skills/.hub/index-cache 2>/dev/null
  rm -rf /root/.npm/_npx/*/node_modules/agent-browser 2>/dev/null
  journalctl --vacuum-size=20M >/dev/null 2>&1 || true
}

# --- 1. CLEANUP (pre-update) ---
cleanup_stage

# --- 2. HERMES SELF-UPDATE ---
echo "--- hermes update ---" | tee -a "$LOG"
VER_BEFORE=$(hermes version 2>/dev/null | head -1)
UPD_OUT=$(hermes update --yes 2>&1)
echo "$UPD_OUT" | tail -20 | tee -a "$LOG"
VER_AFTER=$(hermes version 2>/dev/null | head -1)
echo "version before: $VER_BEFORE" | tee -a "$LOG"
echo "version after:  $VER_AFTER"  | tee -a "$LOG"
if [ "$VER_BEFORE" != "$VER_AFTER" ]; then
  echo "UPDATE_APPLIED: yes" | tee -a "$LOG"
else
  echo "UPDATE_APPLIED: no (already latest)" | tee -a "$LOG"
fi

# --- 2.5 LEAN BACKUP -> private GitHub repo (overwrite daily, no local retention) ---
echo "--- lean backup to github ---" | tee -a "$LOG"
TMP=$(mktemp -d)
BAK="$TMP/$BACKUP_FILE"
# tar ONLY config + skills + profiles (excludes state.db, cache, logs, venv)
tar -czf "$BAK" -C /root/.hermes config.yaml skills profiles 2>/dev/null
if [ -f "$BAK" ]; then
  SZ=$(du -h "$BAK" | cut -f1)
  echo "backup size: $SZ (config.yaml + skills + profiles; excludes state.db/cache/logs)" | tee -a "$LOG"
  # clone (shallow), overwrite file, force-push to main
  CLONE="$TMP/repo"
  if git clone --depth 1 "https://${TOKEN}@github.com/${BACKUP_REPO}.git" "$CLONE" >/dev/null 2>&1; then
    cp "$BAK" "$CLONE/$BACKUP_FILE"
    cd "$CLONE"
    git config user.email "hermes@nousresearch.com"; git config user.name "Hermes Agent"
    git add -A
    git commit -m "lean backup $(date -u +%Y-%m-%dT%H:%M:%SZ)" >/dev/null 2>&1
    if git push --force origin "$BACKUP_BRANCH" >/dev/null 2>&1; then
      echo "BACKUP: uploaded to $BACKUP_REPO ($BACKUP_FILE), local tarball deleted" | tee -a "$LOG"
    else
      echo "BACKUP: push FAILED (check token/repo)" | tee -a "$LOG"
    fi
    cd /root
  else
    echo "BACKUP: clone FAILED (repo unreachable)" | tee -a "$LOG"
  fi
  rm -rf "$TMP"   # deletes local tarball + clone — no local retention
else
  echo "BACKUP: tar failed" | tee -a "$LOG"
fi

# --- 3. CLEANUP AGAIN (post-update) ---
echo "--- post-update cleanup pass ---" | tee -a "$LOG"
cleanup_stage

# --- 4. RESTART dashboard + cloudflared tunnel (pick up new code) ---
echo "--- restart services ---" | tee -a "$LOG"
AGENT_ACTIVE=$(ps -eo args 2>/dev/null | grep -iE "hermes" | grep -v grep \
  | grep -vE "dashboard --host|gateway run|mcp_stdio_watchdog" \
  | grep -vE "hdd_cleanup|hermes update" | wc -l)
if [ "$AGENT_ACTIVE" -gt 0 ]; then
  echo "RESTART: deferred — agent/subagent active ($AGENT_ACTIVE worker proc(s) detected)" | tee -a "$LOG"
  echo "dashboard: (not restarted) | tunnel: (not restarted)" | tee -a "$LOG"
  echo "TUNNEL_URL: (restart skipped)" | tee -a "$LOG"
  echo "HEALTH: (skipped — no restart)" | tee -a "$LOG"
else
  if command -v systemctl >/dev/null 2>&1; then
    systemctl restart hermes-dashboard.service hermes-tunnel.service 2>&1 | tee -a "$LOG"
    sleep 5
    DASH=$(systemctl is-active hermes-dashboard.service)
    TUN=$(systemctl is-active hermes-tunnel.service)
    echo "dashboard: $DASH | tunnel: $TUN" | tee -a "$LOG"
    TURL=$(grep -oiE "https://[a-z0-9.-]+\.trycloudflare\.com" /var/log/cloudflared/tunnel.log 2>/dev/null | tail -1)
    if [ -n "$TURL" ]; then
      echo "TUNNEL_URL: $TURL" | tee -a "$LOG"
    else
      echo "TUNNEL_URL: (not found in log yet)" | tee -a "$LOG"
    fi
    # HEALTH CHECK (#1): is the dashboard actually serving? is the tunnel URL reachable?
    sleep 2
    if curl -sf -o /dev/null "http://127.0.0.1:9119" 2>/dev/null; then
      echo "HEALTH: dashboard HTTP 200 OK" | tee -a "$LOG"
    else
      echo "HEALTH: dashboard NOT responding on :9119 (check service)" | tee -a "$LOG"
    fi
    if [ -n "$TURL" ] && curl -sf -o /dev/null "$TURL" 2>/dev/null; then
      echo "HEALTH: tunnel URL reachable" | tee -a "$LOG"
    elif [ -n "$TURL" ]; then
      echo "HEALTH: tunnel URL NOT reachable ($TURL)" | tee -a "$LOG"
    fi
  else
    echo "systemctl not available; skipping restart" | tee -a "$LOG"
    echo "HEALTH: (skipped)" | tee -a "$LOG"
  fi
fi

sync
sleep 1
AFTER=$(df -h / | awk 'NR==2{print $5" used="$3" avail="$4}')

echo "disk before: $BEFORE" | tee -a "$LOG"
echo "disk after:  $AFTER"  | tee -a "$LOG"
echo "--- top space users ---" | tee -a "$LOG"
find /root -type f -size +20M -exec du -h {} + 2>/dev/null | sort -rh | head -8 | tee -a "$LOG"

echo "done" | tee -a "$LOG"
