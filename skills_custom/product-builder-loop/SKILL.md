---
name: product-builder-loop
description: End-to-end cycle for digital product creation and monetization. Covers ideation (scout), production (build), publication (list), and performance tracking (measure). Use when creating digital products like Notion templates, prompt packs, PDF guides, or Canva templates for sale on Gumroad, PromptBase, or Amazon KDP.
---

# Product Builder Loop: Scout → Build → List → Measure

## Phase 1: SCOUT (Ideation)
1. Query memory for `scout_ideas_iteration_*` entries
2. Score ideas by: automation_score, demand_signal, time_to_revenue, competition_gap
3. Select top idea with highest total_score
4. Validate demand via web search (trends, competitor analysis)
5. Output: Product concept brief (type, target audience, price range)

## Phase 2: BUILD (Production)
Based on product type, use appropriate skill:
- **Notion template** → Use `frontend-design` for mockup, export Notion-compatible Markdown
- **Prompt pack** → Use `skill-creator` patterns for structured prompts
- **PDF guide** → Use `pdf` skill for document generation
- **Canva template** → Use `canvas-design` for visual assets
- **Pptx presentation** → Use `pptx` skill

Quality standards:
- Minimum 5 sections/pages
- Include usage instructions
- Professional formatting (brand-consistent)
- Self-contained (no external dependencies)

## Phase 3: LIST (Publication)
Platforms by product type:
| Product Type | Primary Platform | Secondary |
|:---|:---|:---|
| Notion template | Gumroad ($15 USDC) | Notion Marketplace |
| Prompt pack | PromptBase ($3-10) | Gumroad |
| PDF guide | Gumroad ($9-19) | Amazon KDP |
| Canva template | Canva Marketplace | Gumroad |

Listing requirements:
- Title: SEO-optimized, <60 chars
- Description: 3 benefits + 2 use cases + pricing
- Thumbnail: High-quality visual (use `canvas-design` skill)
- Tags: 5-7 relevant keywords

## Phase 4: MEASURE (Analytics)
Track after 7 days, 14 days, 30 days:
- Views / conversions / revenue
- Update `revenue_by_platform` in memory
- Calculate ROI: (revenue - api_spend) / time_invested
- If ROI < 1.0 after 14 days → pivot or kill

## Integration with Memory
- Save product specs to `vault/02 - Projects/{{product_name}}.md`
- Record listing in `active_listings` in memory
- Update `total_revenue_usd` and `revenue_by_platform` weekly
- Tag failed approaches in `failed_approaches` for learning

## Automation Triggers
- New scouting run: `/scout` command
- Build from selected idea: `/build {{idea_id}}`
- List on platform: `/list {{product_id}} {{platform}}`
- Weekly performance: `/measure`
