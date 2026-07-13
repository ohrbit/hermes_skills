# Recovery: Modal worker I/O wedge → extract from Kanban summaries

When a Modal-sandbox worker's terminal/write_file wedges, the worker usually
still embeds the full designed source in its `kanban show` summary (often under
a `FULL FILE CONTENT:` or `Full file content:` marker, or in a task comment).

## Step 1 — pull the raw summary to a file
```bash
hermes kanban show t_8f70215f 2>&1 > /tmp/engine-raw.txt
hermes kanban show t_bc34b910 2>&1 > /tmp/gfx-raw.txt
hermes kanban show t_7877ea1c 2>&1 > /tmp/ui-raw.txt
```

## Step 2 — extract the code block (Python, run via terminal or execute_code)
```python
import re
txt = open('/tmp/engine-raw.txt').read()
# code starts at the IIFE / comment banner
start = txt.find('/* ===================== GSEngine')
end_marker = txt.find('module.exports=GSEngine;')
nl = txt.find('\n', end_marker)
code = txt[start:nl+1]
# IIFE close is usually MISSING after a wedge — re-append it
if '})(typeof window' not in code:
    code = code.rstrip() + '\n})(typeof window !== "undefined" ? window : this);\n'
open('/tmp/engine.js','w').write(code)
```

For renderer/gfx: find `Full file content:` then cut at the kanban footer
(`\nEvents`, `\n[2026`, or `\nRuns`):
```python
idx = txt.find('Full file content:')
content = txt[idx+len('Full file content:'):]
m = re.search(r'\n\s{2}\[2026|\n\s{2}Runs|\nEvents', content)
if m: content = content[:m.start()]
content = content.strip()
e = content.rfind('}());')
if e>0: content = content[:e+5]
open('/tmp/renderer.js','w').write(content)
```

## Step 3 — reassemble locally (merge step)
Use raw `open()`, NOT `read_file` (read_file prepends `LINE|` and corrupts
JS bitwise ops like `a|=0`). Insert engine + renderer + a mainloop into the
shell's `<script>` placeholder, write `/root/.../index.html`.

## Step 4 — verify
```bash
# syntax
python3 -c "import re;h=open('index.html').read();m=re.search(r'<script>(.*?)</script>',h,re.DOTALL);open('/tmp/f.js','w').write(m.group(1))"
node --check /tmp/f.js && echo OK

# runtime harness with mock DOM/canvas (Node, no browser)
# - global.window = global; stub getElementById -> fake canvas with Proxy ctx
# - replace IIFE close `})(typeof window...)` -> `})(global);` via regex
# - eval, then GSEngine.Engine.evolve({generations:3}) and GSRenderer.draw(mockScene, proxyCtx)
# NOTE: a real <canvas> needs the `canvas` npm lib; Proxy ctx is enough to prove no throw.
```

## Why this works
The Kanban board is the durable IPC channel. Even when a worker can't persist
to disk or egress to the host, its LLM output (the summary) survives in the
board and is readable by the agent locally. Treat the summary as the artifact
transport.
