# KAI-9000 ORCHESTRATOR v2.0.0
## Sovereign Architect Edition

> **Zero Law**: Truth > Agreement. Utility > Impression.

Android + Termux + OpenHuman v0.63.9 автономный мульти-агентный оркестратор.

## Package Contents

| Component | Count | Details |
|:--|:--|:--|
| **Skills** | 32 | 17 Anthropic + 12 Manus + 3 Custom |
| **MCP Servers** | 12 | filesystem, github, sqlite, brave, notion, google-ai, binance, polymarket, asana, gmail, meta-marketing, gworkspace |
| **Workflows** | 3 | morning_crypto_brief, deep_research, tdd_crypto_loop |
| **System Prompt** | 1 | 130 lines, Zero Law + RED TEAM + 6-layer CRYPTO ORACLE |
| **Obsidian Templates** | 4 | daily_brief, project_card, adr, research_note |
| **Install Script** | 1 | Automated 8-step installer for Termux |

## Skills Registry (32)

### Anthropic Skills (17)
pdf, docx, pptx, xlsx, algorithmic-art, brand-guidelines, canvas-design,
doc-coauthoring, frontend-design, internal-comms, mcp-builder, skill-creator,
slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing, claude-api

### Manus Skills (12)
agent-architect, skill-creator, github-gem-seeker, manus-api, excel-generator,
typst-pdf-maker, internet-skill-finder, skills-orchestrator, prompt-digest,
tts-prompter, similarweb-analytics, youtube-video-research

### Custom Skills (3)
crypto-portfolio-monitor (CRYPTO ORACLE enhanced), product-builder-loop, agent-architect

## Architecture

```
KAI-9000
├── Master System Prompt (Zero Law, RED TEAM, CRYPTO ORACLE)
├── Skills (32)
│   ├── anthropic/ (17)
│   ├── manus/ (12)
│   └── custom/ (3)
├── MCP Hub (12 servers)
├── Workflows (3)
│   ├── morning_crypto_brief.yaml (cron 08:00)
│   ├── deep_research.yaml (ATLAS 7-phase, on-demand)
│   └── tdd_crypto_loop.yaml (GitHub issue + cron */15min)
├── Subagents (5)
│   ├── @Architect (code review, TDD, refactoring)
│   ├── @ResearchLead (ATLAS 7-phase, FORENSIC AUDIT)
│   ├── @CryptoStrategist (6-layer analysis, Sovereign Signal)
│   ├── @MeetingExecutive (calendar, transcripts)
│   └── @ProductBuilder (digital products, Gumroad, KDP)
└── Memory
    ├── SQLite (facts + episodes, decay function)
    └── Obsidian Vault (SecondBrain)
```

## Installation (Termux)

```bash
curl -sL https://github.com/romanyukzhenya82-sketch/kai9000-orchestrator/releases/download/v2.0.0/kai9000_package_v2.zip -o /tmp/kai.zip
unzip -o /tmp/kai.zip -d /tmp/kai
bash /tmp/kai/install_scripts/kai9000_install.sh
```

## Manual Steps (after install)

1. Insert API keys in `~/.kai9000/mcp/mcp_servers.toml`
2. Copy `~/.kai9000/system_prompts/master_system_prompt.md` to OpenHuman Settings → Agent → System Prompt
3. Import 3 YAML workflows from `~/.kai9000/workflows/` into TinyFlows

## Connected Projects

- **Hermes Foundation**: 6 trading agents (Long/Short/Spot/Arb/Moonshot/Options), Bybit USDT-M
- **CryptoPrompt Architect**: React + Gemini 2.5, trade prompt generation
- **RepurposeFlow-AI**: Streamlit + Groq, 1 text → 12 platforms
- **Crypto Portfolio Pro**: Gumroad listing ($15 USDC)

## Monetization Strategies
1. GEO Content Factory (Rev-Share)
2. Meta Ads AI Audit (Success Fee)
3. Automation Store (Digital Kits)
4. AI Transformation Agency (High-Ticket)

License: MIT
