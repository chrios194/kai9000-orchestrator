#!/bin/bash
# KAI-9000 ORCHESTRATOR v2.0.0 — INSTALLER
# Sovereign Architect Edition
# 32 Skills | 12 MCP Servers | 3 Workflows

set -e
KAI_DIR="$HOME/.kai9000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== KAI-9000 ORCHESTRATOR v2.0.0 INSTALLATION ===${NC}"

# 1. BASE PACKAGES
echo -e "${GREEN}[1/8] Installing base packages...${NC}"
pkg install -y python nodejs git openssh curl unzip > /dev/null 2>&1 || true

# 2. STRUCTURE
echo -e "${GREEN}[2/8] Creating directory structure...${NC}"
mkdir -p "$KAI_DIR"/{skills/{anthropic,manus,custom},mcp,workflows,vault/{01-Daily,02-Projects,03-Decisions,04-Research},system_prompts}

# 3. CLONE REPO
echo -e "${GREEN}[3/8] Cloning repository...${NC}"
cd /tmp && rm -rf kai9000-orchestrator
git clone https://github.com/romanyukzhenya82-sketch/kai9000-orchestrator.git > /dev/null 2>&1 || true

# 4. COPY SKILLS (32 total)
echo -e "${GREEN}[4/8] Copying 32 skills...${NC}"
cp -r /tmp/kai9000-orchestrator/skills/* "$KAI_DIR/skills/" 2>/dev/null || true

# 5. COPY CONFIGS
echo -e "${GREEN}[5/8] Copying MCP config + workflows + system prompt...${NC}"
cp /tmp/kai9000-orchestrator/mcp_config/mcp_servers.toml "$KAI_DIR/mcp/" 2>/dev/null || true
cp -r /tmp/kai9000-orchestrator/workflows/* "$KAI_DIR/workflows/" 2>/dev/null || true
cp /tmp/kai9000-orchestrator/system_prompts/master_system_prompt.md "$KAI_DIR/system_prompts/" 2>/dev/null || true

# 6. VAULT TEMPLATES
echo -e "${GREEN}[6/8] Setting up Obsidian vault templates...${NC}"
cp -r /tmp/kai9000-orchestrator/obsidian_vault/* "$KAI_DIR/vault/" 2>/dev/null || true

# 7. VERIFY
echo -e "${GREEN}[7/8] Verifying installation...${NC}"
SKILL_COUNT=$(find "$KAI_DIR/skills" -name "SKILL.md" | wc -l)
WORKFLOW_COUNT=$(find "$KAI_DIR/workflows" -name "*.yaml" | wc -l)
MCP_EXISTS=$(test -f "$KAI_DIR/mcp/mcp_servers.toml" && echo "✓" || echo "✗")
PROMPT_EXISTS=$(test -f "$KAI_DIR/system_prompts/master_system_prompt.md" && echo "✓" || echo "✗")

# 8. REPORT
echo -e "${GREEN}[8/8] Installation complete!${NC}"
echo ""
echo "=== KAI-9000 v2.0.0 STATUS ==="
echo "Skills: $SKILL_COUNT (expected: 32)"
echo "Workflows: $WORKFLOW_COUNT (expected: 3)"
echo "MCP Config: $MCP_EXISTS"
echo "System Prompt: $PROMPT_EXISTS"
echo ""

if [ "$SKILL_COUNT" -lt 20 ]; then
    echo -e "${RED}WARNING: Less than 20 skills found. Check git clone output.${NC}"
fi

echo "=== MANUAL STEPS REMAINING ==="
echo "1. Edit $KAI_DIR/mcp/mcp_servers.toml — insert API keys"
echo "2. Copy $KAI_DIR/system_prompts/master_system_prompt.md to OpenHuman Settings"
echo "3. Import workflows from $KAI_DIR/workflows/ into TinyFlows"
echo ""
echo "=== DONE ==="
