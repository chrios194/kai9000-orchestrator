# KAI-9000 MULTI-AGENT ORCHESTRATOR

> **Версия**: 1.0.0 | **Платформа**: Android (Termux) + OpenHuman v0.63.9 | **Статус**: Готов к развёртыванию

## ЧТО ЭТО

KAI-9000 — мульти-агентный оркестратор для Android-смартфона. Выступает «правой рукой» пользователя во всех делах и проектах: трейдинг, разработка, исследования, создание цифровых продуктов.

## СОСТАВ ПАКЕТА

```
kai9000_package/
├── skills_custom/          # 20 навыков (17 Anthropic + 3 кастомных)
│   ├── agent-architect/        # Анализ архитектуры, Karpathy Council
│   ├── crypto-portfolio-monitor/ # Мониторинг aUSDT/XAUt/XLM_PERP
│   ├── product-builder-loop/    # Цикл Scout→Build→List→Measure
│   ├── pdf/                     # PDF генерация
│   ├── docx/                    # Word документы
│   ├── pptx/                    # PowerPoint
│   ├── xlsx/                    # Excel
│   ├── mcp-builder/             # Создание MCP серверов
│   ├── webapp-testing/          # Playwright тестирование
│   ├── skill-creator/            # Создание новых навыков
│   ├── algorithmic-art/          # p5.js арт
│   ├── canvas-design/            # Canvas графика
│   ├── theme-factory/             # CSS/Tailwind темы
│   ├── frontend-design/           # UI/UX
│   ├── web-artifacts-builder/      # React+Tailwind артефакты
│   ├── brand-guidelines/           # Бренд-стиль
│   ├── internal-comms/             # Внутренние коммуникации
│   ├── doc-coauthoring/            # Совместное редактирование
│   ├── claude-api/                 # Anthropic SDK reference
│   └── slack-gif-creator/          # Slack анимации
├── mcp_config/            # Конфиг 8 MCP серверов
│   └── mcp_servers.toml
├── workflows/             # 3 автономных workflow
│   ├── morning_crypto_brief.yaml   # Утренний брифинг (cron 08:00)
│   ├── deep_research.yaml          # Deep Research по запросу
│   └── tdd_crypto_loop.yaml        # TDD разработка + криптомониторинг
├── system_prompts/        # Master System Prompt
│   └── master_system_prompt.md
├── obsidian_vault/        # Шаблоны Obsidian
│   ├── 01_daily/DAILY-TEMPLATE.md
│   ├── 02_projects/PROJECT-TEMPLATE.md
│   ├── 03_decisions/ARCH-TEMPLATE.md
│   └── 04_research/RESEARCH-TEMPLATE.md
├── install_scripts/       # Установочный скрипт
│   └── kai9000_install.sh
└── docs/
    └── README.md          # Этот файл
```

## УСТАНОВКА (3 ШАГА)

### Шаг 1: Перенос на Android
```bash
# Скачай архив kai9000_package.zip на телефон
# Распакуй в Termux:
cd ~
unzip kai9000_package.zip
```

### Шаг 2: Запуск установщика
```bash
cd kai9000_package
bash install_scripts/kai9000_install.sh
```

### Шаг 3: Вставка API-ключей
```bash
nano ~/.kai9000/mcp/mcp_servers.toml
# Замени PLACEHOLDER_* на реальные ключи:
#   - GITHUB_PERSONAL_ACCESS_TOKEN
#   - BRAVE_API_KEY
#   - NOTION_API_KEY
#   - GOOGLE_AI_API_KEY
#   - BINANCE_API_KEY / BINANCE_SECRET
```

## АРХИТЕКТУРА

```
Пользователь
    ↓
KAI-9000 Orchestrator (Android + Termux)
    ├── 20 Skills (17 Anthropic + 3 кастомных)
    ├── 8 MCP Servers (FS, GitHub, SQLite, Brave, Notion, Google AI, Binance, Polymarket)
    ├── 3 Workflows (Morning Brief, Deep Research, TDD+Crypto)
    ├── Memory (SQLite + Obsidian Vault)
    └── 5 Subagents (@Architect, @ResearchLead, @CryptoStrategist, @MeetingExecutive, @ProductBuilder)
```

## НАВЫКИ KAI-9000

### Кастомные (созданы под пользователя)
- **agent-architect**: Анализ архитектуры через Karpathy 3-stage deliberation
- **crypto-portfolio-monitor**: Мониторинг aUSDT/XAUt/XLM_PERP, алерты ликвидации
- **product-builder-loop**: Цикл создания цифровых продуктов (Scout→Build→List→Measure)

### Anthropic skills (готовые)
- **Документы**: pdf, docx, pptx, xlsx
- **Дизайн**: algorithmic-art, canvas-design, theme-factory, frontend-design, web-artifacts-builder, brand-guidelines
- **Разработка**: mcp-builder, webapp-testing, claude-api
- **Коммуникации**: internal-comms, doc-coauthoring, slack-gif-creator
- **Мета**: skill-creator

## WORKFLOWS

1. **Утренний Крипто-Брифинг** (08:00 ежедневно): сбор данных → проверка портфеля → классификация → Telegram дайджест
2. **Deep Research** (по запросу): 4 параллельных запроса → cross-critique → синтез → отчёт в vault
3. **TDD Dev Loop + Crypto Monitor**: GitHub Issue → TDD (RED→GREEN→PR) + каждые 30 мин проверка портфеля

## БЕЗОПАСНОСТЬ

- Read-only операции выполняются автономно
- Деструктивные операции требуют подтверждения пользователя
- Крипто-алерты отправляются только при реальной угрозе (depeg, margin critical)
- API-ключи хранятся в config.toml, не в коде
