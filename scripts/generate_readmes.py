#!/usr/bin/env python3
"""
generate_readmes.py — regenerate a human README.md for every skill in this repo
and rewrite the root README.md as a full index.

Run from the repo root:
    python3 scripts/generate_readmes.py

For each skill folder (one that contains SKILL.md), it writes <skill>/README.md
derived from SKILL.md (name, description, install, contents, category).
Then it rewrites ./README.md as an index of all skills grouped by category.

Idempotent: safe to re-run after adding new skills. Does NOT touch SKILL.md.
"""
import re, os, pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_FILE = "SKILL.md"


def find_skills(root: pathlib.Path):
    skills = []
    for skill_md in root.rglob("SKILL.md"):
        folder = skill_md.parent
        rel = folder.relative_to(root)
        parts = rel.parts
        if len(parts) < 2:
            continue  # skip stray SKILL.md at root
        category, name = parts[0], parts[1]
        skills.append((category, name, folder, skill_md))
    return sorted(skills)


def parse_frontmatter(md: str):
    name = desc = tags = when = ""
    m = re.search(r"^name:\s*(.+)$", md, re.M)
    name = m.group(1).strip() if m else ""
    m = re.search(r"^description:\s*(.+)$", md, re.M)
    desc = m.group(1).strip() if m else ""
    m = re.search(r"^tags:\s*(.+)$", md, re.M)
    tags = m.group(1).strip() if m else ""
    wm = re.search(r"##\s*When to use\s*\n(.*?)(?=\n##\s|\Z)", md, re.S)
    when = wm.group(1).strip() if wm else ""
    return name, desc, tags, when


def subsection(title, body):
    return body.strip()


def build_skill_readme(name, desc, cat, when):
    disp = name or cat
    out = f"# {disp}\n\n"
    out += (desc.strip() if desc else "Hermes Agent skill.") + "\n\n"
    out += "## What it does\n"
    out += "This skill is defined in [`SKILL.md`](./SKILL.md). "
    if when:
        out += "Use it for: " + when.strip()[:300].replace("\n", " ") + ".\n"
    else:
        out += "See SKILL.md for the full specification, steps, and pitfalls.\n"
    out += "\n## Install\n```bash\nhermes skills install " + name + "\n```\n\n"
    out += "## Contents\n"
    out += "- `SKILL.md` — the skill definition (frontmatter + instructions)\n"
    out += "- `references/` — deep-dive docs and code\n"
    out += "- `templates/` — prompt / body templates\n"
    out += "- `scripts/` — runnable helpers\n\n"
    out += f"## Category\n`{cat}`\n\n---\n"
    out += "*This README was generated from `SKILL.md` by scripts/generate_readmes.py.*\n"
    return out


def build_root_readme(skills):
    cats = {}
    for category, name, folder, skill_md in skills:
        md = skill_md.read_text(errors="ignore")
        n, d, t, w = parse_frontmatter(md)
        cats.setdefault(category, []).append({"name": n or name, "desc": d, "tags": t})

    out = "# hermes_skills\n\n"
    out += "A curated collection of [Hermes Agent](https://hermes-agent.nousresearch.com) skills. "
    out += "Each skill lives in `category/skill-name/` with a `SKILL.md` (the definition) and a "
    out += "human-readable `README.md`.\n\n"
    out += "## Install\n```bash\nhermes skills tap add ohrbit/hermes_skills\nhermes skills install <skill-name>\n```\n\n"
    out += f"## Skills ({sum(len(v) for v in cats.values())})\n\n"
    for cat in sorted(cats):
        out += f"### {cat}\n\n"
        out += "| Skill | Description |\n|---|---|\n"
        for meta in sorted(cats[cat], key=lambda m: m["name"]):
            d = (meta["desc"] or "").strip().replace("\n", " ")
            if len(d) > 160:
                d = d[:157] + "..."
            out += f"| **{meta['name']}** | {d} |\n"
        out += "\n"
    out += "## Layout\n```\nhermes_skills/\n"
    out += "├── README.md            # this file (index of all skills)\n"
    out += "├── scripts/generate_readmes.py  # regenerate all READMEs\n"
    out += "└── <category>/\n    └── <skill>/\n        ├── README.md\n        ├── SKILL.md\n        ├── references/\n        ├── templates/\n        └── scripts/\n```\n\n"
    out += "## Notes\n- Skills follow the [agentskills.io](https://agentskills.io) convention.\n"
    out += "- Per-skill READMEs are generated from `SKILL.md`; extend them as needed.\n"
    out += "- Regenerate after adding skills: `python3 scripts/generate_readmes.py`\n"
    return out


def main():
    root = REPO_ROOT
    skills = find_skills(root)
    if not skills:
        print("No skills found (no SKILL.md under category/skill/).")
        return
    written = 0
    for category, name, folder, skill_md in skills:
        md = skill_md.read_text(errors="ignore")
        n, d, t, w = parse_frontmatter(md)
        readme = build_skill_readme(n or name, d, category, w)
        (folder / "README.md").write_text(readme)
        written += 1
        print(f"  README -> {category}/{name}")
    root_readme = build_root_readme(skills)
    (root / "README.md").write_text(root_readme)
    print(f"✅ Wrote {written} skill READMEs + root index.")


if __name__ == "__main__":
    main()
