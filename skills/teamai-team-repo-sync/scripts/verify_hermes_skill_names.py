#!/usr/bin/env python3
"""Scan teamai team-repo skills: name/dir mismatch, missing SKILL.md, empty description.

usage: python3 verify_hermes_skill_names.py [skills_dir]
       default: /root/.teamai/team-repo/skills
exit 0 = clean, 1 = issues found (JSON on stdout)
"""
import os, re, sys, json

base = sys.argv[1] if len(sys.argv) > 1 else "/root/.teamai/team-repo/skills"

def fm(md_path):
    t = open(md_path, encoding="utf-8", errors="replace").read()
    m = re.match(r"\A---\n(.*?)\n---", t, re.DOTALL)
    if not m:
        return None, None, "no-frontmatter"
    name = desc = None
    for line in m.group(1).splitlines():
        if line.startswith("name:"):
            name = line[5:].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            desc = line[12:].strip().strip('"').strip("'")
    return name, desc, "ok"

issues = {"mismatch": [], "missing": [], "empty-desc": []}
for d in sorted(os.listdir(base)):
    p = os.path.join(base, d)
    if not os.path.isdir(p):
        continue
    md = os.path.join(p, "SKILL.md")
    if not os.path.isfile(md):
        issues["missing"].append(d)
        continue
    name, desc, ok = fm(md)
    if ok != "ok" or name is None:
        issues["mismatch"].append({"dir": d, "reason": ok})
    elif name != d:
        issues["mismatch"].append({"dir": d, "name": name})
    if not desc:
        issues["empty-desc"].append(d)

print(json.dumps(issues, ensure_ascii=False, indent=1))
print(f"total: mismatch={len(issues['mismatch'])} missing={len(issues['missing'])} empty-desc={len(issues['empty-desc'])}")
sys.exit(1 if any(issues.values()) else 0)
