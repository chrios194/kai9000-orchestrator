# AIOS Core

Central orchestration core for isolated AI content operations.

## Architecture

- **Channels are isolated.** Every job, research record, opportunity analysis, review, content brief, and workflow event is scoped to a channel.
- **LLM routing is role-based.** Planner/researcher/writer/reviewer/fallback roles resolve to configured models through the LiteLLM-compatible transport.
- **Integration adapters are provider-neutral.** Research, generation, media, publishing, analytics, and knowledge adapters expose a common execution contract. Provider credentials and implementations stay outside core.
- **Execution context is mandatory.** LLM and integration calls require a channelId; job-bound routing additionally verifies the job's channel.
- **Approval remains explicit.** Jobs can only move from reviewing to approved through the approval API.
- **Neon is persistence.** The existing production workflow schema is used; this core does not perform automatic destructive migrations.

## Configuration

Model roles can be supplied with createAIOS({ models: { ... } }) or environment variables:

- AIOS_PLANNER_MODEL
- AIOS_RESEARCH_MODEL
- AIOS_WRITER_MODEL
- AIOS_REVIEWER_MODEL
- AIOS_FALLBACK_MODEL
- AIOS_DEFAULT_MODEL

LiteLLM-compatible transport uses:

- LITELLM_BASE_URL
- LITELLM_API_KEY

Integration configuration is passed through createAIOS({ integrations: { research, generation, media, publishing, analytics, knowledge } }).

The core intentionally does not hardcode provider secrets or external service credentials.