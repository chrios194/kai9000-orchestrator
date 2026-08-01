---
name: agent-architect
description: Analyzes software architecture, reviews code structure, and proposes refactoring strategies. Use when facing architectural decisions, code review tasks, or system design challenges across any tech stack. Implements Karpathy 3-stage deliberation protocol for architectural decisions.
---

# Agent Architect: Architecture Analysis & Review

## When to Use
- User asks to review or audit a codebase
- Architectural decision needed (database choice, framework, pattern)
- Refactoring plan required
- System design from scratch

## Process

### Step 1: Context Gathering
Before proposing any architecture:
1. Read the project's existing structure (directories, entry points, configs)
2. Identify the tech stack (languages, frameworks, dependencies)
3. Check for existing architecture documentation (README, docs/, ARCHITECTURE.md)
4. Query memory (SQLite Memory Tree, Jolli) for prior architectural decisions on this project

### Step 2: Karpathy 3-Stage Deliberation
For any non-trivial architectural decision:

#### Stage 1 — First Principles (2-3 competing approaches)
Generate 2-3 distinct approaches without anchoring on defaults:
- Approach A: [describe with trade-offs]
- Approach B: [describe with trade-offs]
- Approach C: [describe with trade-offs]

#### Stage 2 — Peer Critique
For each approach, evaluate:
- Scalability bottlenecks
- Security vulnerabilities
- Maintenance overhead
- Migration complexity
- Performance under load

#### Stage 3 — Synthesis
Select the strongest elements and combine into a single solution:
- Final decision with justification
- Migration plan if applicable
- Risk mitigation steps

### Step 3: Output Format
Always produce:
1. **Architecture Diagram** (Mermaid graph)
2. **Component Table** (name, responsibility, tech, dependencies)
3. **Decision Record** (ADR format: context → alternatives → decision → consequences)
4. **Action Items** (ordered, with effort estimates)

## Integration with Memory
After completing an architectural review:
- Save ADR to `vault/03 - Decisions/` with `#decision #architecture` tags
- Record key decisions in SQLite Memory Tree via `memory_store`
- Create Jolli memory entry with git context

## Constraints
- Never propose architecture you cannot verify with evidence
- Always cite specific files, functions, or configs as evidence
- If information is incomplete, state what is missing and how to get it
