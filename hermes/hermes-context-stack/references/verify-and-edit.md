# Context-stack verify & edit — exact commands

## Enumerate ALL context files (never default-only)
```
find /root/.hermes -iname "SOUL.md" -o -iname "user.md" -o -iname ".hermes.md" -o -iname "AGENTS.md"
```

## Report each with size + mtime (sort by time)
```
find /root/.hermes -iname "SOUL.md" -printf "%T+ %6s  %p\n" | sort
```
Real example from one host (sizes in bytes):
- 513  /root/.hermes/SOUL.md            (stock default)
- 513  /root/.hermes/profiles/calypso/SOUL.md   (stock)
- 16851 /root/.hermes/profiles/sirvir/SOUL.md   (HEAVILY customized — the real persona)
- 30005 /root/.hermes/profiles/sirvir/AGENTS.md
- 1370 /root/.hermes/memories/USER.md

## Active profile
```
echo "HERMES_PROFILE=${HERMES_PROFILE:-<unset>}"
```
unset ⇒ default profile runs (reads ~/.hermes/SOUL.md, not the profile dirs).

## Byte-perfect install / replace (long single-line SOUL content)
Source often a cached upload: /root/.hermes/cache/documents/doc_*.md
```python
import shutil
shutil.copyfile(SRC, "/root/.hermes/SOUL.md")
```
Verify: `wc -c /root/.hermes/SOUL.md` then head/tail diff vs source.

## Lineage note (domain context)
The default SOUL on this host referenced `=>[OMNICOMP2]` and `OptmzdSkllchn`.
OMNICOMP = "OmniCompetent" — descends from the **Proteus** mega-prompt
(arXiv:2306.0055, Stoltz 2023; created by Sam Witten as "Proteus 4.2 - OmniCompetent
Assistant"). Proteus introduced the single-large-prompt ("Mega prompt") architecture:
role adoption (`***ChatGPT*** adopts the ROLE of ***Proteus***`), GOAL0..N hierarchy, and a
compressed symbolic skill-chain language. The user's custom SOUL is a direct evolution
of that design. Useful when the user references SOUL lineage, OMNICOMP, or Proteus.
