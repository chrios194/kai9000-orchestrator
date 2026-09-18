# AIOS Core — Active Task

## Task
Complete and verify the central AIOS orchestration workflow.

## Checklist
- [x] Channel-scoped execution context and isolation
- [x] Role-based LLM routing with fallback
- [x] Provider-neutral integration registry
- [x] Research, opportunity, review, and content-brief persistence paths
- [x] GitHub Actions workflow configured
- [x] Runtime validation hardened for workflow state and channel-scoped inputs
- [x] LLM client hardened with timeout, safe error parsing, and optional request fields
- [x] Neon analysis/review writes made idempotent
- [x] Provider registry rejects unknown providers
- [x] CI workflow includes syntax, schema verification, and tests
- [ ] GitHub Actions run reports passing syntax and tests
- [ ] Enable/confirm GitHub Actions on this fork and execute the first run

## Workflow
File: `.github/workflows/aios-core.yml`

Triggers:
- push to `main`
- pull request to `main`
- manual `workflow_dispatch`

CI steps:
1. Checkout repository
2. Install Node 20 dependencies
3. `npm run syntax`
4. `npm run migrate`
5. `npm test`

## Hardening completed
The checklist items covering routing, provider/integration boundaries, persistence, LLM client handling, Neon idempotency, provider validation, and CI configuration have been hardened with additional validation and regression tests. CI is still the final external verification gate.

## Current blocker
The repository is a fork. GitHub reports no workflow runs and no commit statuses for the latest commits. Forked repositories do not run Actions by default until Actions is enabled for the fork. The connected GitHub tooling can inspect and modify repository files but cannot dispatch a new workflow run from this session.

Manual execution:
1. Enable GitHub Actions for the fork under repository Settings → Actions → General.
2. Open the AIOS Core workflow.
3. Run workflow on `main`.
4. After the run exists, inspect its job and logs before marking CI complete.

## Constraints
- Preserve independent channel isolation.
- Do not expose or commit credentials.
- Do not modify the Neon schema without explicit approval.
- Do not claim CI success until GitHub reports a completed run.

## Note
GitHub Issues are disabled for this repository, so this task is tracked in-repository instead of as an Issue.
