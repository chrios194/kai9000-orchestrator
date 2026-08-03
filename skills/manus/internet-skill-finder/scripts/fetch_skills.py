#!/usr/bin/env python3
"""Fetch skill lists from GitHub repositories."""
import json, os, subprocess, urllib.request
from pathlib import Path

REPOSITORIES = {
    "anthropics/skills": {"skills_path": "skills", "branch": "main", "type": "skills"},
    "obra/superpowers": {"skills_path": "skills", "branch": "main", "type": "skills"},
    "vercel-labs/agent-skills": {"skills_path": "skills", "branch": "main", "type": "skills"},
    "K-Dense-AI/claude-scientific-skills": {"skills_path": "scientific-skills", "branch": "main", "type": "skills"},
    "ComposioHQ/awesome-claude-skills": {"skills_path": ".", "branch": "master", "type": "skills"},
    "travisvn/awesome-claude-skills": {"branch": "main", "type": "curated_list"},
    "BehiSecc/awesome-claude-skills": {"branch": "main", "type": "curated_list"},
}

def check_gh_cli():
    try:
        r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except:
        return False

def fetch_repo(repo, info):
    api_url = f"https://api.github.com/repos/{repo}/contents/{info.get('skills_path','')}"
    req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req) as resp:
        items = json.loads(resp.read())
    return [i["name"] for i in items if i["type"] == "dir"]

def main():
    cache_file = Path(__file__).parent.parent / "references" / "skills_cache.json"
    results = {}
    for repo, info in REPOSITORIES.items():
        try:
            skills = fetch_repo(repo, info)
            results[repo] = {"skills": skills, "url": f"https://github.com/{repo}"}
            print(f"✓ {repo}: {len(skills)} skills")
        except Exception as e:
            print(f"✗ {repo}: {e}")
    cache_file.write_text(json.dumps(results, indent=2))
    print(f"\nCache saved to {cache_file}")

if __name__ == "__main__":
    main()
