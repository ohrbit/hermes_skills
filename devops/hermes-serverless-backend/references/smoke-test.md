# Modal Backend Smoke Test

Verifies the Modal `terminal.backend` actually spins up sandboxes. Export the
token vars (or rely on Hermes `.env` since the SDK reads them from env).

```bash
export MODAL_TOKEN_ID=ak-XXXX
export MODAL_TOKEN_SECRET=as-XXXX
python3 <<'PY'
import modal, time
try:
    m = modal.Client.from_env()
    print("client OK:", type(m).__name__)
    app = modal.App.lookup("hermes-smoke", create_if_missing=True)
    t0 = time.time()
    sb = modal.Sandbox.create(app=app, timeout=300)
    print("sandbox up in %.1fs id=%s" % (time.time()-t0, sb.object_id))
    # separate args = NO shell expansion:
    p = sb.exec("echo", "hello-from-modal")
    print("STDOUT:", p.stdout.read().strip())
    # for shell expansion use bash -c:
    # p2 = sb.exec("bash", "-c", "echo $(date -u)")
    sb.terminate()
    print("SMOKE_OK")
except Exception as e:
    import traceback; traceback.print_exc()
    print("SMOKE_FAIL:", repr(e)[:200])
PY
```

Expected output:
```
client OK: Client
sandbox up in 0.2s id=sb-...
STDOUT: hello-from-modal
SMOKE_OK
```

Observed on first setup (2026-07-11): cold start 0.2s, exec returned
literal args (no expansion), terminate clean. All green.
