---
name: setup-bundle
description: Reproduction bundle for the full operational Hermes stack on a fresh Debian 13 box — nightly maintenance script, cloudflared tunnel systemd unit, and a step-by-step SETUP.md. Use when rebuilding Hermes on a new machine, or to understand the operational setup (cleanup + update + backup + restart).
category: devops
tags: [setup, reproduction, maintenance, backup, systemd, tunnel, debian]
version: 1.0.0
---

# Setup Bundle

Reproduce the complete Hermes operational stack on a fresh Debian 13 machine.

## What it contains
- `scripts/hdd_cleanup.sh` — nightly: disk cleanup → `hermes update` → lean GitHub backup → post-cleanup → systemd restart (+health check, +agent-activity guard)
- `systemd/hermes-tunnel.service` — cloudflared quick-tunnel unit (NOT auto-created by Hermes install)
- `SETUP.md` — full 6-phase reproduction guide

## When to use
- Standing up Hermes on a new VBox / server
- Understanding what the nightly cron actually does
- Recovering a box from the private backup/config repos

## The 6 phases (see SETUP.md for commands)
1. Install Hermes (`curl … install.sh`)
2. Tunnel unit (install cloudflared + copy unit)
3. Pull the 14 skills (`hermes skills tap add ohrbit/hermes_skills`)
4. Identity from private `ohrbit/hermes-config` (SOUL.md + USER.md)
5. Nightly maintenance (copy script + recreate cron + `GITHUB_TOKEN` in `.env`)
6. Secrets (GitHub token, Modal/Daytona, Telegram/Discord, Stripe)

## Key repos
- `ohrbit/hermes_skills` — skills + this bundle (public)
- `ohrbit/hermes_backups` — private, lean nightly backup (overwritten daily)
- `ohrbit/hermes-config` — private, SOUL.md + USER.md

## Notes
- The maintenance script never touches `state.db`, whisper cache, runtimes, or `obsidian-vault`.
- The tunnel URL changes daily — captured in the nightly Telegram report.
- `GITHUB_TOKEN` must have `repo` scope for backups + config pull.
