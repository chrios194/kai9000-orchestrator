---
name: skill-creator
description: Guide for creating or updating skills that extend the agent via specialized knowledge, workflows, or tool integrations.
---

# Skill Creator

## Overview
Гайд по созданию/обновлению skills. MUST read this skill BEFORE modifying any skill.

## Workflow
1. `init_skill.py <name>` — creates skill from template
2. Write SKILL.md with frontmatter (name, description)
3. Add scripts/ and references/ as needed
4. `quick_validate.py <name>` — validate structure

## Skill Structure
```
<skill-name>/
  SKILL.md          # Documentation with YAML frontmatter
  scripts/          # Executable Python scripts
  references/       # Reference docs and data
  assets/           # Templates and static files
```

## Frontmatter Requirements
- `name`: skill identifier (lowercase, hyphens)
- `description`: what the skill does and WHEN to use it

## Anti-Patterns
- Don't create skills that duplicate existing ones
- Don't put executable logic in SKILL.md — use scripts/
- Don't create overly broad skills — be specific
