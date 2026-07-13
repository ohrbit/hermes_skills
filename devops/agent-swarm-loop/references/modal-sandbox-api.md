# Modal Sandbox API — gotchas (modal python SDK v1.3.4)

Verified against the installed SDK (`pip show modal` → 1.3.4). The old
`Mount.from_local_file` seen in `credential_files.py` / older skill drafts is
**PRIVATE / broken** here; and `Sandbox.create` expects a command *list*, not a
shell string. Capture these so a future swarm run doesn't re-derive them.

## ⚠️ `Sandbox.create` command must be a LIST, not a shell string
```python
# WRONG — dumb-init treats the whole string as one executable →
#   "[dumb-init] echo START; ...: No such file or directory"
modal.Sandbox.create("echo START; which git ssh; echo END", image=img, ...)

# RIGHT — pass each argv token as a separate string
modal.Sandbox.create("bash", "-lc", "echo START; which git ssh; echo END",
                     image=img, ...)
```
All entrypoint args must be strings (a *list* of strings, not nested lists).

## ⚠️ Mount a local file: use `Image.add_local_file`, NOT `Mount.from_local_file`
`modal.Mount` has no public constructor (`.from_local_file` is `_from_local_file`,
private) and `modal.Mount()` raises "Class _Mount has no constructor". Bake the
file into the image instead:
```python
import modal
img = (modal.Image.debian_slim()
        .apt_install("git", "openssh-client")
        .add_local_file("/root/.hermes/swarm_tunnel_derby_keys.json",
                         remote_path="/root/.hermes/swarm_tunnel_derby_keys.json"))
sb = modal.Sandbox.create("bash", "-lc",
        "cat /root/.hermes/swarm_tunnel_derby_keys.json",
        image=img, timeout=180)
sb.wait()
print(sb.stdout.read())
```
This lands the real file (no redaction — it's a file, not tool-call text).

## Reading sandbox stdout/stderr
`sb.stdout.read()` / `sb.stderr.read()` only return after `sb.wait()`. If a
sandbox errors, check `sb.stderr.read()` — the failure reason is there (e.g.
missing executable, command not found).

## Verified minimal smoke test
```python
import modal
app = modal.App.lookup("hermes-agent-swarm", create_if_missing=True)
img = modal.Image.debian_slim().apt_install("git", "openssh-client")
sb = modal.Sandbox.create("bash", "-lc", "git --version && echo OK",
                          image=img, timeout=120)
sb.wait()
print(sb.returncode, sb.stdout.read())
```
Exit 0 + "OK" = Modal workers can clone/push via a mounted deploy key.

## `terminal.credential_files` — VERIFIED working
`credential_files` IS injected into every Modal sandbox (verified in the
Tunnel-Derby run: a file declared in `config.yaml` under
`terminal.credential_files` showed up at its remote path inside the sandbox with
real, non-redacted content). It is the clean way to deliver the deploy-key
keystore. `Image.add_local_file` is the alternative (file baked into the image).

Write the key into `~/.ssh` inside the sandbox (git/SSH need it there, not at the
JSON path). Worker recipe (run INSIDE the sandbox):
```python
# import json, os
# d = json.load(open('/root/.hermes/swarm_tunnel_derby_keys.json'))
# p = os.path.expanduser('~/.ssh/id_ed25519')
# os.makedirs(os.path.dirname(p), exist_ok=True)
# open(p,'w').write(d['<YOUR_ROLE>']); os.chmod(p,0o600)
# os.environ['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no -i '+p
```
NEVER inline the keystore in the `delegate_task` context/prompt — Hermes redacts
private-key text in tool-call args to `[REDACTED PRIVATE KEY]` and the push fails
with `Permission denied (publickey)`. Mount it; let the worker READ it from the file.

## Image build note
`Image.debian_slim().apt_install(...).add_local_file(...)` builds a fresh image per
call (20-60s first build, then cached). Reuse the same `app` name
(`modal.App.lookup("hermes-agent-swarm", create_if_missing=True)`) across runs so
image layers cache.
