# Worker-timeout / partial-push recovery (learned R4, Tunnel Derby)

A `delegate_task` worker can **time out (600s) after it has already pushed a
branch but BEFORE it finishes its self-test / summary**. The branch exists on the
remote but may be EMPTY (no files) or carry only part of the work. The Orchestrator
must NOT re-dispatch blindly — it should take over the unfinished module locally.

## Step 1 — verify what actually landed on the remote branch
```bash
# does the branch exist?
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/owner/repo/branches/feat/r4-flight-physicist" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('EXISTS' if 'name' in d else 'MISSING')"
# does the target FILE exist on that branch?
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/owner/repo/contents/tunnel-derby/physics.mjs?ref=feat/r4-flight-physicist" \
  -o /tmp/phys.json
python3 -c "import json,base64; d=json.load(open('/tmp/phys.json')); print('LINES:',len(base64.b64decode(d['content']).decode().splitlines())) if 'content' in d else print('NO FILE:', d.get('message'))"
```
If `NO FILE` / `Not Found` → the worker died before committing. Take over (Step 2).

## Step 2 — the Orchestrator takes over locally
Take the worker's LAST GOOD source from a prior successful branch (e.g. the r3
version of the same module), apply the intended fix yourself, and push directly
via the GitHub API (no worker needed). This is faster and more reliable than
re-dispatching.

```python
import urllib.request, json, base64, requests
TOK = open("/root/.hermes/.env").read().split("GITHUB_TOKEN=")[1].split("\n")[0]
hdr = {"Authorization": f"Bearer {TOK}"}

# 1. fetch last-good source from a prior branch
req = urllib.request.Request(
    "https://api.github.com/repos/owner/repo/contents/tunnel-derby/physics.mjs?ref=feat/r3-flight-physicist",
    headers=hdr)
src = base64.b64decode(json.load(urllib.request.urlopen(req))["content"]).decode()

# 2. apply the fix locally
src = src.replace("const CURVE_FORCE = 30;", "const CURVE_FORCE = 50;")
# ... apply soft-failure / clamp / look-ahead patch ...

# 3. create the r4 branch from the r3 tip + commit the file
sha = json.load(urllib.request.urlopen(urllib.request.Request(
    "https://api.github.com/repos/owner/repo/git/ref/heads/feat/r3-flight-physicist", headers=hdr)))["object"]["sha"]
requests.post("https://api.github.com/repos/owner/repo/git/refs",
    headers={**hdr, "Content-Type": "application/json"},
    json={"ref": "refs/heads/feat/r4-flight-physicist", "sha": sha})
cur = json.load(urllib.request.urlopen(urllib.request.Request(
    "https://api.github.com/repos/owner/repo/contents/tunnel-derby/physics.mjs?ref=feat/r3-flight-physicist", headers=hdr)))
blob_sha = cur["sha"]
content = base64.b64encode(src.encode()).decode()
requests.put("https://api.github.com/repos/owner/repo/contents/tunnel-derby/physics.mjs",
    headers={**hdr, "Content-Type": "application/json"},
    json={"message": "r4: <fix description>", "content": content, "sha": blob_sha,
          "branch": "feat/r4-flight-physicist"})
```
Then run the Orchestrator-sweep harness on the assembled branches to validate.

## Why this is better than re-dispatching
- A re-dispatch risks the SAME 600s timeout on the same slow operation.
- The Orchestrator has the real branches already; patching locally + pushing via API
  is deterministic and seconds-fast.
- You keep full control of the fix (no "worker guessed the constant").
