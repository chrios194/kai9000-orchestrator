#!/usr/bin/env python3
"""Quick validation for skills."""
import sys, re
from pathlib import Path

def validate(skill_path):
    path = Path(skill_path)
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"
    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "Missing YAML frontmatter"
    if "name:" not in content:
        return False, "Missing 'name' in frontmatter"
    if "description:" not in content:
        return False, "Missing 'description' in frontmatter"
    return True, "✓ Valid skill"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: quick_validate.py <skill-path>")
        sys.exit(1)
    ok, msg = validate(sys.argv[1])
    print(msg)
    sys.exit(0 if ok else 1)
