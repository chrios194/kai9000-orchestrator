#!/usr/bin/env python3
"""
Agent Architect — Scaffold Agent
Автоматизированный сборщик структуры нового AI-агента.
"""
import argparse, json, os, sys
from datetime import datetime
from pathlib import Path

MODULES_CATALOG = {
    "planner": {"name": "Planner Module", "tag": "planner_module",
        "prompt_block": "<planner_module>\n- System equipped with planner for task planning\n- Plans use numbered pseudocode\n</planner_module>"},
    "knowledge": {"name": "Knowledge Module", "tag": "knowledge_module",
        "prompt_block": "<knowledge_module>\n- Knowledge and memory module for best practices\n</knowledge_module>"},
    "datasource": {"name": "Datasource Module", "tag": "datasource_module",
        "prompt_block": "<datasource_module>\n- API client for external data\n</datasource_module>"},
}

def scaffold(name, role, domain, modules, tools, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    # system_prompt.md
    prompt = f"# {name.upper()} AGENT\n\n## ROLE\n{role}\n## DOMAIN\n{domain}\n\n"
    for m in modules:
        if m in MODULES_CATALOG:
            prompt += MODULES_CATALOG[m]["prompt_block"] + "\n"
    
    (out / "system_prompt.md").write_text(prompt)
    
    # tools.json
    (out / "tools.json").write_text(json.dumps(tools, indent=2))
    
    # agent_config.json
    config = {"name": name, "role": role, "domain": domain,
              "modules": modules, "created": datetime.now().isoformat()}
    (out / "agent_config.json").write_text(json.dumps(config, indent=2))
    
    print(f"✓ Agent scaffolded at {out}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--domain", required=True)
    p.add_argument("--modules", default="planner,knowledge")
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    scaffold(args.name, args.role, args.domain, 
             args.modules.split(","), [], args.output_dir)
