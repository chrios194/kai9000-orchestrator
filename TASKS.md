# AIOS Core — Active Task

## Task
Complete and verify the central AIOS orchestration workflow.

## Checklist
- [x] Channel-scoped execution context and isolation
- [x] Role-based LLM routing with fallback
- [x] Provider-neutral integration registry
- [x] Research, opportunity, review, and content-brief persistence paths
- [x] GitHub Actions workflow configured
- [ ] GitHub Actions run reports passing syntax and tests

## Workflow
File: `.github/workflows/aios-core.yml`

Triggers:
- push to `main`
- pull request to `main`
- manual `workflow_dispatch`

CI steps:
1. Checkout repository
2. Install Node 20
3. `npm install`
4. `npm run syntax`
5. `npm test`

## Constraints
- Preserve independent channel isolation.
- Do not expose or commit credentials.
- Do not modify the Neon schema without explicit approval.

## Note
GitHub Issues are disabled for this repository, so this task is tracked in-repository instead of as an Issue.
