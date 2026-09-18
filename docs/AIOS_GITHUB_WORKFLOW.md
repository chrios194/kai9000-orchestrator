# AIOS GitHub Workflow

## Canonical flow

1. **Task intake** — define one outcome, acceptance criteria, dependencies and target repository.
2. **Assignment** — task receives a stable ID and is assigned to the integration owner/agent.
3. **Branch** — create a task branch from `main`: `task/<id>-<short-name>`.
4. **Implement** — change only the assigned scope.
5. **Validate** — unit/integration tests plus MCP Inspector smoke tests where an MCP integration is involved.
6. **Review** — inspect diff, security, secrets, channel isolation and regression risk.
7. **Pull request** — PR references the task ID and records validation results.
8. **Merge** — merge only after required checks pass.
9. **Post-merge verification** — verify the integration against the live/target interface.
10. **Closeout** — record what changed, what remains, and the next task.

## Repository roles

- `AIOS-CORE-`: central architecture/specification and shared orchestration contracts.
- `kai9000-orchestrator`: executable orchestration/integration implementation.
- `AIOS-Channel-01-Cashvolt`: isolated CashVolt channel implementation and assets.
- Provider repositories/forks: reference code only; do not treat them as part of the AIOS runtime unless explicitly integrated.

## Non-negotiable boundaries

- Channel repositories remain independent.
- Provider credentials never enter Git.
- MCP is the interoperability layer; provider-specific logic belongs behind integration adapters.
- No direct copying of provider repositories into the orchestrator.
- No automatic merge until CI/validation is established.
- Legacy or unrelated workflows stay out of the core execution path.

## MCP standard

Use official MCP SDKs and the MCP Inspector as the compatibility/testing baseline. The Inspector supports Web, CLI and TUI modes, and its CLI is designed for CI and coding-agent validation.

## Task naming

`<priority>-<area>-<short-name>`

Examples:
- `P0-mcp-foundation`
- `P0-channel-isolation`
- `P1-youtube-publishing`

## Completion rule

A task is not complete because code was written. It is complete only when the implementation, validation, security review and integration contract are all recorded.
