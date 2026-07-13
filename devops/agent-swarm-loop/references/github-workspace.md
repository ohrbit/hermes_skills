# GitHub Workspace — per-Agent Deploy-Key Provisioning

The clean dev-team model: the Orchestrator mints one SSH deploy key per agent,
registers the PUBLIC key on the shared repo, and passes the PRIVATE key to the
agent via `delegate_task` context (or `kanban` task body). The agent clones via
`git@github.com:owner/repo.git`, works on a branch, opens a PR.

## Why deploy keys (not PATs)
- GitHub **PATs cannot be created via API** (only Web-UI / authenticated user API,
  which here can only *see* our own token, not mint new ones).
- **Deploy keys CAN**: `POST /repos/{owner}/{repo}/keys` with `read_only:false`
  creates a repo-scoped, revocable credential. One per agent = isolation by design.
- Modal containers inherit **no host env** — secrets reach them only via a
  **file mount** (`terminal.credential_files` or `Image.add_local_file`).
  ⚠️ **NEVER inline a private key in the sub-agent context / kanban body** —
  Hermes redacts secrets embedded in tool-call text to `[REDACTED PRIVATE KEY]`,
  so the worker receives an empty key and the git push fails with
  `Permission denied (publickey)`. Mount the keyfile instead (see Worker side).

## Provisioning (Orchestrator side, Python — proven POC)

```python
import json, subprocess, tempfile, os, urllib.request
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
ENV = (HERMES_HOME / ".env").read_text()
GITHUB_TOKEN = [l.split("=",1)[1] for l in ENV.splitlines()
                if l.startswith("GITHUB_TOKEN=")][0]
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}",
           "Accept": "application/vnd.github+json",
           "User-Agent": "hermes-swarm", "Content-Type": "application/json"}

def provision_agent_key(repo: str, agent_name: str) -> str:
    """Create SSH key pair, register pub key as deploy key, return PRIV key text."""
    with tempfile.TemporaryDirectory() as d:
        key = Path(d) / "id_ed25519"
        subprocess.run(["ssh-keygen","-t","ed25519","-N","","-C",
                        f"swarm-{agent_name}", "-f", str(key)],
                       capture_output=True, text=True, check=True)
        pub = (key.with_suffix(".pub")).read_text().strip()
        priv = key.read_text()
        body = {"title": f"swarm-{agent_name}-{os.getpid()}",
                "key": pub, "read_only": False}
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/keys",
            data=json.dumps(body).encode(), headers=HEADERS, method="POST")
        with urllib.request.urlopen(req) as r:
            dk = json.loads(r.read().decode())
        # stash id for later cleanup
        (HERMES_HOME / "swarm_keys.jsonl").open("a").write(
            json.dumps({"repo": repo, "agent": agent_name,
                        "key_id": dk["id"]}) + "\n")
        return priv

def revoke_agent_key(repo: str, key_id: int) -> None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/keys/{key_id}",
        headers=HEADERS, method="DELETE")
    urllib.request.urlopen(req)  # 204 on success
```

## Worker side (inside the agent)
The private key is **mounted as a file** (NOT inlined in the prompt — it would be
redacted). Orchestrator registers `swarm_keys.json` via `terminal.credential_files`
or bakes it into the Modal image with `Image.add_local_file(path, remote_path=...)`.
Worker reads its own role's key out of that JSON:

```python
import json, os
keys = json.load(open("/root/.hermes/swarm_tunnel_derby_keys.json"))
priv = keys["<YOUR_ROLE>"]            # e.g. "flight-physicist"
p = os.path.expanduser("~/.ssh/id_ed25519")
os.makedirs(os.path.dirname(p), exist_ok=True); os.chmod(os.path.dirname(p), 0o700)
open(p,"w").write(priv); os.chmod(p, 0o600)
```
Then in shell:
```bash
export GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519"
git clone git@github.com:OWNER/REPO.git /tmp/work
cd /tmp/work && git checkout -b feat/<round>-<role>
# ... do work, commit, push, open PR ...
```
If the worker ever sees `[REDACTED PRIVATE KEY]` in its prompt, that is the
redaction trap — abort the inlined-key path and tell the orchestrator to mount
the keyfile instead.

## Alternative: shared master token (Option A)
If isolation isn't required, add `.env` to `terminal.credential_files` so Modal
mounts `~/.hermes/.env` into every container. Write as a **real YAML list via
python** — `hermes config set terminal.credential_files [...]` serialises the
list as a STRING and breaks it.

```python
import yaml
p = Path.home()/".hermes"/"config.yaml"
c = yaml.safe_load(p.read_text())
c.setdefault("terminal",{})["credential_files"] = [".env"]
p.write_text(yaml.safe_dump(c, sort_keys=False))
```
Worker then reads `GITHUB_TOKEN` from `~/.hermes/.env` and uses HTTPS clone.

## Cleanup
On loop end, revoke every deploy key (read `swarm_keys.jsonl`), delete ephemeral
profiles, remove the jsonl. Leaving keys is a credential leak.
