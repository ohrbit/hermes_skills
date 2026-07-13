# JIT worker task-body template (Kanban-as-IPC — no upload plumbing)

Copy per worker. Replace `<ROLE>` / `<SPEC>` / `<FILE>` / `<EXPORT>`.

```text
You are the <ROLE> specialist for <PROJECT>.

PROTOCOL — deliver via the Kanban board, NOT file upload:
  Write your output to /tmp/<FILE> using write_file.
  When done, COMPLETE the task with:  kanban_complete(summary=cat /tmp/<FILE>)
  The summary MUST contain the FULL file content so the merge worker can use it.

BUILD <SPEC>:
  - <bullet 1>
  - <bullet 2>
  - Export <EXPORT> (e.g. window.Foo)

STUDY: <reference URL, e.g. a sibling project's index.html>
SKILL: <relevant skill, e.g. fable-style-singlefile-web>
AFTER: kanban_complete(summary=cat /tmp/<FILE>) — verify the summary shows the full source.
```

## Merge-worker body (parented)
```text
MERGE specialist: assemble the final file from <N> parent tasks.

1. This task auto-promotes from todo→ready when all parents are done.
2. Fetch each parent's full file content from its kanban summary:
     hermes kanban show t_<UI>   → has shell.html in summary
     hermes kanban show t_<ENG>  → has engine.js in summary
     hermes kanban show t_<GFX>  → has renderer.js in summary
3. Extract the file contents from the summaries.
4. ASSEMBLE: base shell + insert engine + insert renderer + wire mainloop.
   Single file, zero dependencies, no CDN.
5. Write /tmp/index.html, then:
     kanban_complete(summary=cat /tmp/index.html)

SKILL: fable-style-singlefile-web
STUDY: <reference project>
```

## Dispatch (bash)
```bash
t_ui=$(hermes kanban create "PJ: UI & Shell" --assignee gs-ui --goal --goal-max-turns 8 --body "$(cat ui-body.txt)")
t_eng=$(hermes kanban create "PJ: Engine" --assignee gs-engine --goal --goal-max-turns 10 --body "$(cat eng-body.txt)")
t_gfx=$(hermes kanban create "PJ: GFX" --assignee gs-gfx --goal --goal-max-turns 8 --body "$(cat gfx-body.txt)")
hermes kanban create "PJ: Merge" --assignee gs-merge --goal --goal-max-turns 6 \
  --parent "$t_ui" "$t_eng" "$t_gfx" --body "$(cat merge-body.txt)"
```
