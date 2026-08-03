---
name: prompt-digest
description: Manage the Prompt Engineering Daily Digest pipeline. LangGraph-based system collecting, analyzing, and sending daily Telegram digests about prompt engineering.
---

# Prompt Digest

## Pipeline
1. Collect sources (Twitter, Reddit, arXiv, blogs)
2. Analyze and score with LLM
3. Generate digest summary
4. Send via Telegram

## Tech
- LangGraph for pipeline orchestration
- Telegram Bot API for delivery
- LLM for content analysis and scoring
