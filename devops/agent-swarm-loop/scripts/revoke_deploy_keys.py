#!/usr/bin/env python3
"""
revoke_deploy_keys.py — delete all deploy keys logged in ~/.hermes/swarm_keys.jsonl.

Usage: python3 revoke_deploy_keys.py

Reads each {repo,agent,key_id} line and DELETEs /repos/{repo}/keys/{key_id}.
Run at swarm end so no credential leaks remain. Failed revocations are kept in
the log for a retry; a clean run deletes the log file.
"""
import json, urllib.request
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"


def gh_token():
    env = (HERMES_HOME / ".env").read_text()
    return [l.split("=", 1)[1] for l in env.splitlines() if l.startswith("GITHUB_TOKEN=")][0]


def main():
    token = gh_token()
    log = HERMES_HOME / "swarm_keys.jsonl"
    if not log.exists():
        print("nothing to revoke")
        return
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "User-Agent": "hermes-swarm"}
    kept = []
    for line in log.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        req = urllib.request.Request(
            f"https://api.github.com/repos/{rec['repo']}/keys/{rec['key_id']}",
            headers=headers, method="DELETE")
        try:
            with urllib.request.urlopen(req) as r:
                print(f"  [OK] revoked {rec['agent']} (id={rec['key_id']}) HTTP {r.status}")
        except urllib.error.HTTPError as e:
            print(f"  !! failed {rec['agent']} id={rec['key_id']} HTTP {e.code}")
            kept.append(line)
    if kept:
        log.write_text("\n".join(kept) + "\n")
    else:
        log.unlink()
        print("cleaned up swarm_keys.jsonl")


if __name__ == "__main__":
    main()
