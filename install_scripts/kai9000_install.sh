#!/bin/bash
set -e

echo "=========================================="
echo "  KAI-9000 ORCHESTRATOR INSTALLER v1.0.0"
echo "  Android + Termux + OpenHuman"
echo "=========================================="

# 1. Установка пакетов
echo "[1/8] Установка пакетов..."
pkg install -y git python python-pip nodejs curl wget unzip jq

# 2. Создание директорий
echo "[2/8] Создание структуры каталогов..."
mkdir -p ~/.kai9000/{skills,mcp,workflows,vault/system_prompts,docs,install_scripts}
mkdir -p ~/.kai9000/vault/{01_daily,02_projects,03_decisions,04_research,05_reference}

# 3. Клонирование репозитория
echo "[3/8] Клонирование KAI-9000..."
cd /tmp
rm -rf kai9000-orchestrator
git clone --depth 1 https://github.com/romanyukzhenya82-sketch/kai9000-orchestrator.git
cd kai9000-orchestrator

# 4. Установка 20 навыков
echo "[4/8] Установка 20 навыков..."
cp -r skills_custom/* ~/.kai9000/skills/
SKILL_COUNT=$(ls ~/.kai9000/skills/ | wc -l)
echo "  Установлено навыков: $SKILL_COUNT"

# 5. Установка 3 workflows
echo "[5/8] Установка 3 workflows..."
cp workflows/*.yaml ~/.kai9000/workflows/
WF_COUNT=$(ls ~/.kai9000/workflows/ | wc -l)
echo "  Установлено workflows: $WF_COUNT"

# 6. Установка MCP конфигурации
echo "[6/8] Установка MCP конфигурации..."
cp mcp_config/mcp_servers.toml ~/.kai9000/mcp/

# 7. Установка master system prompt
echo "[7/8] Установка master system prompt..."
cp system_prompts/master_system_prompt.md ~/.kai9000/vault/system_prompts/

# 8. Установка Obsidian vault шаблонов
echo "[8/8] Установка Obsidian vault шаблонов..."
cp -r obsidian_vault/* ~/.kai9000/vault/ 2>/dev/null || true

# Копирование README и install script
cp docs/README.md ~/.kai9000/docs/
cp install_scripts/kai9000_install.sh ~/.kai9000/install_scripts/

# Верификация установки
echo ""
echo "=========================================="
echo "  ПРОВЕРКА УСТАНОВКИ"
echo "=========================================="

ERRORS=0

if [ "$SKILL_COUNT" -ne 20 ]; then
  echo "ОШИБКА: Ожидалось 20 навыков, gefundenо $SKILL_COUNT"
  ERRORS=$((ERRORS+1))
fi

if [ "$WF_COUNT" -ne 3 ]; then
  echo "ОШИБКА: Ожидалось 3 workflow, gefundenо $WF_COUNT"
  ERRORS=$((ERRORS+1))
fi

if [ ! -f ~/.kai9000/mcp/mcp_servers.toml ]; then
  echo "ОШИБКА: MCP конфиг не найден"
  ERRORS=$((ERRORS+1))
fi

if [ ! -f ~/.kai9000/vault/system_prompts/master_system_prompt.md ]; then
  echo "ОШИБКА: Master system prompt не найден"
  ERRORS=$((ERRORS+1))
fi

echo ""
echo "Структура ~/.kai9000/:"
find ~/.kai9000 -maxdepth 2 -type d | sort
echo ""
echo "Навыки: $(ls ~/.kai9000/skills/ | wc -l)"
echo "Workflows: $(ls ~/.kai9000/workflows/ | wc -l)"
echo "MCP config: $([ -f ~/.kai9000/mcp/mcp_servers.toml ] && echo 'OK' || echo 'MISSING')"
echo "System prompt: $([ -f ~/.kai9000/vault/system_prompts/master_system_prompt.md ] && echo 'OK' || echo 'MISSING')"
echo ""

if [ "$ERRORS" -eq 0 ]; then
  echo "=========================================="
  echo "  УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО"
  echo "=========================================="
  echo ""
  echo "ОСТАЛОСЬ (вручную):"
  echo "  1. Вставить API-ключи в ~/.kai9000/mcp/mcp_servers.toml"
  echo "     (GITHUB_TOKEN, BRAVE_API_KEY, GOOGLE_AI_API_KEY, BINANCE_API_KEY)"
  echo "  2. Скопировать master_system_prompt.md в OpenHuman:"
  echo "     cat ~/.kai9000/vault/system_prompts/master_system_prompt.md"
  echo "     Settings → Agent → System Prompt"
  echo "  3. Импортировать workflows в TinyFlows:"
  echo "     ~/.kai9000/workflows/morning_crypto_brief.yaml"
  echo "     ~/.kai9000/workflows/deep_research.yaml"
  echo "     ~/.kai9000/workflows/tdd_crypto_loop.yaml"
else
  echo "ОШИБОК: $ERRORS — проверьте вывод выше"
fi
