# Setup Bundle — reproduce the full Hermes stack on a fresh Debian 13 box

This folder contains the files needed to rebuild the operational Hermes setup from scratch:
the nightly maintenance script, the cloudflared tunnel systemd unit, and this guide.

## What's in here
- `scripts/hdd_cleanup.sh` — nightly cleanup + update + lean GitHub backup + restart(+health)
- `systemd/hermes-tunnel.service` — cloudflared quick-tunnel unit (NOT auto-created by Hermes install)
- `SETUP.md` — this file

## Prerequisites
- Fresh Debian 13 (or similar)
- A GitHub token with `repo` scope (for skills publish + backups + config pull)
- Optional: Modal/Daytona token, Telegram/Discord bot tokens, Stripe key (calypso only)

---

## Phase 1 — Install Hermes
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes login   # or set provider token via `hermes config`
```
This creates `~/.hermes/`, and the `hermes-dashboard` + `hermes-gateway` systemd units.

## Phase 2 — Tunnel unit (manual — not auto-generated)
```bash
# install cloudflared binary
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/bin/cloudflared
chmod +x /usr/bin/cloudflared

# copy the unit from this bundle
cp systemd/hermes-tunnel.service /etc/systemd/system/hermes-tunnel.service
systemctl daemon-reload
systemctl enable --now hermes-dashboard hermes-gateway hermes-tunnel
```
The tunnel assigns a fresh `*.trycloudflare.com` URL on every restart — capture it from the nightly report.

## Phase 3 — Pull the 14 skills
```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install agent-swarm-loop jit-agent-teams kanban-orchestrator \
  model-selection-and-jit-routing hermes-serverless-backend hermes-context-stack \
  github-readme-authoring nano-banana-prompting bayesian-reasoning isaac-lab-bridge \
  github-repo-ingest gitingest-usage hermes-voice-local third-party-skill-evaluation
```

## Phase 4 — Identity (SOUL.md + USER.md) from private repo
```bash
TOKEN=<your-github-token>
git clone https://${TOKEN}@github.com/ohrbit/hermes-config.git /tmp/hc
cp /tmp/hc/default/SOUL.md /root/.hermes/SOUL.md
cp /tmp/hc/default/USER.md /root/.hermes/memories/USER.md
rm -rf /tmp/hc
# verify the active profile (HERMES_PROFILE unset => default loads ~/.hermes/SOUL.md)
echo "HERMES_PROFILE=${HERMES_PROFILE:-<unset>}"
```

## Phase 5 — Nightly maintenance
```bash
# copy the script
cp scripts/hdd_cleanup.sh /root/.hermes/scripts/hdd_cleanup.sh
chmod +x /root/.hermes/scripts/hdd_cleanup.sh

# write the GitHub token (read-guarded .env; append via terminal, never read_file/patch)
printf '\nGITHUB_TOKEN=<your-token>\n' >> /root/.hermes/.env

# recreate the cron job (paste into Hermes chat or run via hermes cron create):
#   name: nightly-hdd-cleanup
#   schedule: 0 3 * * *
#   prompt: "Run /root/.hermes/scripts/hdd_cleanup.sh and report: disk before/after,
#            hermes update version diff + top-5 feature highlights, backup uploaded size+repo,
#            services active state (defer if agent active), health (dashboard HTTP 200 +
#            tunnel URL reachable), tunnel URL. Flag free<1.0G. Do not delete state.db/
#            whisper/runtimes/obsidian-vault."
#   deliver: origin
```

## Phase 6 — Secrets (manual, never automated)
| Secret | Where | Notes |
|---|---|---|
| `GITHUB_TOKEN` | `/root/.hermes/.env` | repo scope; backups + skills publish + config pull |
| Modal/Daytona | `hermes config set terminal.backend modal` + `.env` | only if using serverless backend |
| Telegram/Discord | `hermes gateway` setup | messaging integration |
| Stripe | calypso stack only | not core |

---

## What the maintenance script does (summary)
1. **Cleanup (pre)** — hermes logs, JIT archives, skills index cache, npx caches, journald vacuum
2. **Hermes update** — `hermes update --yes` (git pull + reinstall)
3. **Lean backup** — tar `config.yaml`+`skills`+`profiles` (~40M) → force-push to private `ohrbit/hermes_backups` → delete local (no retention)
4. **Cleanup (post)** — reclaim update-generated cruft
5. **Restart + health** — `systemctl restart hermes-dashboard hermes-tunnel` (guarded: skips if agent/subagent active), then `curl` health check on :9119 + tunnel URL

**Never touches:** `state.db`, whisper model cache, runtimes, `obsidian-vault`.

## Repos involved
- `ohrbit/hermes_skills` — the 14 skills + this bundle (public)
- `ohrbit/hermes_backups` — private, lean nightly backups (overwritten daily)
- `ohrbit/hermes-config` — private, SOUL.md + USER.md (default profile)
