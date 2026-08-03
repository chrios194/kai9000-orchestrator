#!/usr/bin/env python3
"""Skill Initializer - Creates a new skill from template."""
import sys
from pathlib import Path

SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Explain what this skill does and when to use it.]
---

# {skill_title}

## Overview
[TODO: 1-2 sentences explaining what this skill enables]

## When to Use
[TODO: Specific scenarios that trigger this skill]
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: init_skill.py <skill-name>")
        sys.exit(1)
    name = sys.argv[1]
    skill_dir = Path(name)
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(skill_name=name, skill_title=name.replace("-"," ").title()))
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    print(f"✓ Skill '{name}' created at {skill_dir}/")

if __name__ == "__main__":
    main()
