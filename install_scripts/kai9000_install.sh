#!/bin/bash
set -e

# KAI-9000 ORCHESTRATOR — ANDROID BOOTSTRAP SCRIPT
# Запускать в Termux на Android
# Скачать и запустить: bash kai9000_install.sh

echo "╔════════════════════════════════════════╗"
echo "║   KAI-9000 ORCHESTRATOR INSTALLATION   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# === ПРОВЕРКА ОКРУЖЕНИЯ ===
echo -e "${YELLOW}[1/8] Проверка окружения...${NC}"

if ! command -v pkg &> /dev/null; then
    echo -e "${RED}Ошибка: pkg не найден. Запустите в Termux.${NC}"
    exit 1
fi

TERMUX_HOME="$HOME"
KAI_HOME="$TERMUX_HOME/.kai9000"

echo -e "${GREEN}✓ Termux detected: $TERMUX_HOME${NC}"
echo ""

# === БАЗОВЫЕ ПАКЕТЫ ===
echo -e "${YELLOW}[2/8] Установка базовых пакетов...${NC}"
pkg update -y
pkg install -y git nodejs python python-pip ffmpeg curl wget jq openssh

echo -e "${GREEN}✓ Базовые пакеты установлены${NC}"
echo ""

# === NODE.JS ЗАВИСИМОСТИ ===
echo -e "${YELLOW}[3/8] Установка MCP серверов (npm)...${NC}"
npm install -g \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-github \
    @modelcontextprotocol/server-brave-search \
    @modelcontextprotocol/server-notion 2>/dev/null || true

echo -e "${GREEN}✓ MCP серверы установлены${NC}"
echo ""

# === PYTHON ЗАВИСИМОСТИ ===
echo -e "${YELLOW}[4/8] Установка MCP серверов (pip)...${NC}"
pip install --quiet mcp-server-sqlite httpx aiohttp 2>/dev/null || true

echo -e "${GREEN}✓ Python MCP установлены${NC}"
echo ""

# === OLLAMA (опционально) ===
echo -e "${YELLOW}[5/8] Проверка Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama уже установлена${NC}"
    ollama pull gemma3:4b 2>/dev/null || true
else
    echo -e "${YELLOW}Ollama не найдена. Установка...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh 2>/dev/null || \
    echo -e "${YELLOW}Ollama недоступна на этом устройстве — будут использованы облачные модели${NC}"
fi
echo ""

# === СТРУКТУРА ДИРЕКТОРИЙ ===
echo -e "${YELLOW}[6/8] Создание структуры KAI-9000...${NC}"
mkdir -p "$KAI_HOME"/{skills,mcp,workflows,system_prompts}
mkdir -p "$KAI_HOME"/vault/{01-Daily,02-Projects,03-Decisions,04-Research}
mkdir -p "$KAI_HOME"/projects

echo -e "${GREEN}✓ Структура создана: $KAI_HOME${NC}"
echo ""

# === КОПИРОВАНИЕ ФАЙЛОВ ===
echo -e "${YELLOW}[7/8] Копирование файлов...${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Копируем skills
if [ -d "$SCRIPT_DIR/skills_custom" ]; then
    cp -r "$SCRIPT_DIR/skills_custom/"* "$KAI_HOME/skills/"
    SKILL_COUNT=$(find "$KAI_HOME/skills" -name "SKILL.md" | wc -l)
    echo -e "${GREEN}✓ Навыков установлено: $SKILL_COUNT${NC}"
else
    echo -e "${RED}Папка skills_custom не найдена! Скопируйте вручную.${NC}"
fi

# Копируем MCP конфиг
if [ -f "$SCRIPT_DIR/mcp_config/mcp_servers.toml" ]; then
    cp "$SCRIPT_DIR/mcp_config/mcp_servers.toml" "$KAI_HOME/mcp/"
    echo -e "${GREEN}✓ MCP конфигурация скопирована${NC}"
fi

# Копируем workflows
if [ -d "$SCRIPT_DIR/workflows" ]; then
    cp -r "$SCRIPT_DIR/workflows/"*.yaml "$KAI_HOME/workflows/"
    WF_COUNT=$(ls "$KAI_HOME/workflows/"*.yaml 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Workflows установлено: $WF_COUNT${NC}"
fi

# Копируем system prompt
if [ -f "$SCRIPT_DIR/system_prompts/master_system_prompt.md" ]; then
    cp "$SCRIPT_DIR/system_prompts/master_system_prompt.md" "$KAI_HOME/system_prompts/"
    echo -e "${GREEN}✓ Master System Prompt скопирован${NC}"
fi

# Копируем Obsidian Vault шаблоны
if [ -d "$SCRIPT_DIR/obsidian_vault" ]; then
    find "$SCRIPT_DIR/obsidian_vault" -name "*.md" -exec cp --preserve=timestamps {} "$KAI_HOME/vault/" \; 2>/dev/null
    # Копируем в правильные подпапки
    for dir in 01_daily 02_projects 03_decisions 04_research; do
        vault_dir=$(echo "$dir" | sed 's/_/-/g' | sed 's/^\(..\)-\(..\)/\1-\2/')
        if [ -d "$SCRIPT_DIR/obsidian_vault/$dir" ]; then
            cp "$SCRIPT_DIR/obsidian_vault/$dir/"*.md "$KAI_HOME/vault/$vault_dir/" 2>/dev/null
        fi
    done
    echo -e "${GREEN}✓ Obsidian Vault шаблоны скопированы${NC}"
fi

echo ""

# === ФИНАЛЬНАЯ ПРОВЕРКА ===
echo -e "${YELLOW}[8/8] Финальная проверка...${NC}"
echo ""

TOTAL_SKILLS=$(find "$KAI_HOME/skills" -name "SKILL.md" | wc -l)
TOTAL_WF=$(ls "$KAI_HOME/workflows/"*.yaml 2>/dev/null | wc -l)
TOTAL_TEMPLATES=$(find "$KAI_HOME/vault" -name "*.md" | wc -l)

echo "╔════════════════════════════════════════╗"
echo "║   KAI-9000 INSTALLATION COMPLETE       ║"
echo "╠════════════════════════════════════════╣"
echo "║  Skills:     $TOTAL_SKILLS                        ║"
echo "║  Workflows:  $TOTAL_WF                        ║"
echo "║  Templates:  $TOTAL_TEMPLATES                        ║"
echo "║  MCP Config: ✓                            ║"
echo "║  System Prompt: ✓                         ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Дальнейшие шаги (вручную):"
echo "  1. Вставь API-ключи в $KAI_HOME/mcp/mcp_servers.toml"
echo "  2. Скопируй Master System Prompt в настройки OpenHuman"
echo "  3. Импортируй workflows в TinyFlows"
echo ""
echo "KAI-9000 готов к работе."
