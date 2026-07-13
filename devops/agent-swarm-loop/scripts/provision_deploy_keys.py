#!/usr/bin/env python3
"""
provision_deploy_keys.py — mint per-agent SSH deploy keys for a swarm loop.

For each role: ssh-keygen ed25519 -> register PUB key as a GitHub deploy key
(scoped to ONE repo, read/write). Writes ALL priv keys into a single JSON file
that the orchestrator then MOUNTS into the Modal sandbox / credential_files.
The worker reads ITS role's key from that mounted file.

NEVER inline a priv key in a worker prompt — Hermes redacts secrets in
tool-call text to `[REDACTED PRIVATE KEY]` and the git push fails with
`Permission denied (publickey)`. Mount the keystore file instead.

Usage:
  python3 provision_deploy_keys.py --repo ohrbit/FABLE-SHOWCASE \
      --subdir tunnel-derby \
      --roles flight-physicist ga-breeder tunnel-architect renderer
"""
import argparse, json, subprocess, tempfile, urllib.request
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"


def gh_token() -> str:
    env = (HERMES_HOME / ".env").read_text()
    return [l.split("=", 1)[1] for l in env.splitlines() if l.startswith("GITHUB_TOKEN=")][0]


def gh(method, path, token, body=None):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "User-Agent": "hermes-swarm", "Content-Type": "application/json"}
    req = urllib.request.Request(f"https://api.github.com{path}",
        data=json.dumps(body).encode() if body else None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


def provision(repo, subdir, roles, token, keystore_path=None):
    out = {}
    for role in roles:
        with tempfile.TemporaryDirectory() as td:
            key = Path(td) / "id_ed25519"
            subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-C", f"swarm-{role}",
                            "-f", str(key)], capture_output=True, text=True, check=True)
            pub = (key.with_suffix(".pub")).read_text().strip()
            priv = key.read_text()
            st, dk = gh("POST", f"/repos/{repo}/keys", token,
                        {"title": f"swarm-{subdir}-{role}", "key": pub, "read_only": False})
            if st not in (200, 201):
                print(f"  !! {role} FAILED {st} {dk}")
                continue
            with (HERMES_HOME / "swarm_keys.jsonl").open("a") as f:
                f.write(json.dumps({"repo": repo, "agent": role, "key_id": dk["id"], "subdir": subdir}) + "\n")
            out[role] = priv
            print(f"  [OK] {role}: key id={dk['id']}")
    keystore = keystore_path or (
        HERMES_HOME / "swarm_tunnel_derby_keys.json" if subdir == "tunnel-derby"
        else HERMES_HOME / f"swarm_{subdir}_keys.json")
    keystore.write_text(json.dumps(out, indent=2))
    print(f"\n{len(out)} keys -> {keystore}")
    print("MOUNT this file (terminal.credential_files or Image.add_local_file). Do NOT inline in prompts.")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--subdir", required=True)
    ap.add_argument("--roles", nargs="+", required=True)
    ap.add_argument("--keystore", default=None, help="override keystore path")
    args = ap.parse_args()
    provision(args.repo, args.subdir, args.roles, gh_token(),
              keystore_path=Path(args.keystore) if args.keystore else None)


if __name__ == "__main__":
    main()
