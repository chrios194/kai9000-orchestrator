---
name: internet-skill-finder
description: Search and recommend Agent Skills from verified GitHub repositories. Use when finding or recommending skills for specific tasks.
---

# Internet Skill Finder

## Overview
Поиск Agent Skills из 7 проверенных GitHub репозиториев.

## Repositories Monitored
1. anthropics/skills (50K+ stars)
2. obra/superpowers
3. vercel-labs/agent-skills
4. K-Dense-AI/claude-scientific-skills
5. ComposioHQ/awesome-claude-skills
6. travisvn/awesome-claude-skills
7. BehiSecc/awesome-claude-skills

## Priority
1. GitHub Connector (gh CLI) — 15000 req/hr
2. Offline Cache — instant
3. Personal Token — 5000 req/hr

## Scripts
- `scripts/fetch_skills.py` — fetch from GitHub repos or use cache
- `references/skills_cache.json` — offline cache of 7 repos
