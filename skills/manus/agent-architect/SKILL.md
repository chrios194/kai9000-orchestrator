---
name: agent-architect
description: Engineering framework for building autonomous AI agents. Creates new specialized agents with defined architecture, tools, and behavior logic.
---

# Agent Architect

## Overview
Инженерный фреймворк для проектирования и автоматизированной сборки автономных AI-агентов.

## When to Use
- Создание нового специализированного агента
- Определение архитектуры, инструментов и логики поведения
- Scaffold структуры агента из спецификации

## Workflow
1. **Define Agent Parameters**: name, role, domain, modules, tools
2. **Run scaffold_agent.py**: generates system_prompt.md, tools.json, agent_config.json, README.md
3. **Validate**: check structure completeness

## Available Modules
- **Planner Module**: пошаговое планирование, псевдокод, отслеживание статуса
- **Knowledge Module**: база знаний и best practices
- **Datasource Module**: API для данных, Python-клиент ApiClient

## Tool Registry (24 tools)
message_notify_user, message_ask_user, file_read, file_write, file_str_replace, 
file_find_in_content, file_find_by_name, shell_exec, shell_view, shell_wait, 
shell_write_to_process, shell_kill_process, browser_view, browser_navigate, 
browser_restart, browser_click, browser_input, browser_move_mouse, 
browser_press_key, browser_select_option, browser_scroll_up, browser_scroll_down, 
browser_console_exec, browser_console_view, info_search_web, deploy_expose_port, 
deploy_apply_deployment, make_manus_page, idle

## Scripts
- `scripts/scaffold_agent.py` — автоматическая сборка структуры агента
- `references/tools_spec.json` — 24 инструмента в формате OpenAI function calling
- `references/modules.md` — спецификация модулей (Planner/Knowledge/Datasource)
- `references/system_prompt_template.txt` — шаблон системного промпта
