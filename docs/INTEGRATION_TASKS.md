# AIOS Integration Task Board

## P0 — MCP foundation
**Owner:** Orchestrator integration agent  
**Goal:** establish one canonical MCP integration contract using official MCP components.  
**Dependencies:** none.  
**Acceptance:** SDK strategy, server inventory, secret policy, Inspector smoke-test procedure.

## P0 — MCP validation
**Owner:** QA/integration agent  
**Goal:** add repeatable MCP `tools/list` and targeted smoke tests.  
**Dependencies:** MCP foundation.  
**Acceptance:** validation can run locally/CI without exposing credentials.

## P0 — Integration inventory cleanup
**Owner:** Architecture agent  
**Goal:** classify every current integration as CORE, OPTIONAL, LEGACY or REMOVE.  
**Dependencies:** MCP foundation.  
**Acceptance:** one canonical inventory; no duplicate provider adapters.

## P0 — Channel isolation
**Owner:** Channel architecture agent  
**Goal:** enforce independent repository/config/data boundaries for CashVolt and every future channel.  
**Dependencies:** integration inventory.  
**Acceptance:** central orchestration can monitor/coordinate without merging channel state.

## P1 — GitHub delivery pipeline
**Owner:** DevOps agent  
**Goal:** standardize task branch → validation → PR → review → merge.  
**Dependencies:** MCP validation.  
**Acceptance:** protected, repeatable delivery path.

## P1 — Neon persistence adapter
**Owner:** Data integration agent  
**Goal:** define the database boundary for task state, analytics metadata and orchestration state.  
**Dependencies:** channel isolation.

## P1 — Vercel control plane
**Owner:** Deployment agent  
**Goal:** define deployment boundary for dashboard/control-plane components.  
**Dependencies:** GitHub delivery pipeline.

## P1 — Research/search adapter
**Owner:** Research agent  
**Goal:** consolidate web/research providers behind a single interface rather than hard-wiring individual search services.

## Deferred / optional
- Gmail
- Google Workspace
- Asana
- Meta Marketing
- Binance
- Polymarket
- crypto-specific automation

These are not part of the AIOS core path unless a later task explicitly requires them.
