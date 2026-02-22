[PRD.md](https://github.com/user-attachments/files/25463363/PRD.md)
# Autumn v2 — Product Requirements Document

## Product Overview

Autumn is an AI-powered workflow library that monitors YouTube automation channels, extracts structured blueprints from video transcripts using Claude, and presents them as interactive, browsable guides. v2 transforms the frontend from a dashboard-style catalog into a visual, editorial-quality library where each blueprint reads like an actionable guide you can immediately start implementing.

## Target User

You and your team — people building automations who want a curated, scannable library of workflow blueprints they can actually implement. Autumn is your internal documentation and reference guide that's constantly searching for and improving its knowledge of what to build and how.

## What v1 Solved vs. What v2 Solves

- **v1:** Extraction — turning hours of YouTube video content into structured data
- **v2:** Comprehension and action — making that data feel like something you'd actually read, understand, and use

## MVP Features

1. **Content quality overhaul** — Rewrite Claude extraction prompts so titles, summaries, and descriptions are specific and human-readable. Every workflow card should tell you what it does, what problem it solves, and why you'd care — in plain language, not AI filler.

2. **Layout and navigation rebuild** — Replace the tab-heavy dashboard SPA with a React app using sidebar navigation. Visual, spacious, editorial feel inspired by Linear's spatial clarity, warmed up with Autumn's brand palette and heavier grain texture. Feels like a curated field guide.

3. **Interactive blueprint detail pages** — Each workflow's detail page leads with a full-width left-to-right pipeline visualization (CSS/SVG). Every node is clickable, every tool links to its platform, every step links to relevant resources. Decision points highlighted where multiple sources diverge. Setup requirements inline with direct signup/API key links.

4. **Canonical workflows** — Auto-detect when multiple videos cover the same workflow pattern. Synthesize a canonical version that takes the best from each source, with decision points where creators diverge ("Creator A uses Make.com, Creator B uses n8n — here's why"). Canonical workflows improve automatically as new scans find related content.

5. **Save and collect** — Bookmark workflows to a personal collection with notes. Saved workflows are candidates for enrichment when future scans find related content.

## Non-Goals / Out of Scope (v2)

- Team access / deployment beyond local network
- User accounts / authentication / multi-user
- Homepage / discovery redesign (next phase — home feed is functional but not optimized)
- Backend rewrite (Python/Flask stays)
- Database engine change (SQLite stays)
- Major pipeline changes (extraction depth is good, just prompt tuning for presentation)
- Mobile optimization
- The 7-stage status tracking system (simplified into save/collect)
- Setup checklists as a separate tracked feature (folded into inline detail page content)

## User Flows

### Flow 1: Browse & Scan (Home → List)

1. Open Autumn → land on home feed showing a mix of recent workflows, canonical workflow updates, and high-value finds
2. Scan workflow cards — each has a specific headline (e.g., "Automate client onboarding with Airtable + Make.com + Gmail"), a plain-language one-liner, tool icons, and a mini pipeline preview
3. Filter/search by tool, use case, or keyword
4. Click into any workflow for the full blueprint

### Flow 2: Learn & Understand (Detail Page)

1. Hero: full-width left-to-right pipeline visualization — what goes in, what happens at each stage, what comes out
2. Each pipeline node is clickable → shows the tool, what it does at that step, config details, and a direct link to the platform
3. Below the visualization: step-by-step implementation guide with every tool linked, every action described, setup requirements inline
4. Decision points visually called out where sources diverge, with source attribution and reasoning
5. Sidebar or inline: tools needed with direct links (signup, API key pages), cost estimates, free vs. paid

### Flow 3: Save & Collect

1. While viewing a workflow, save it to personal collection
2. Add notes/context when saving (e.g., "useful for the client onboarding project")
3. Saved workflows appear in a dedicated Saved view
4. When future scans find related content, saved workflows are candidates for enrichment

### Flow 4: Jump Off & Do

1. Click any tool name anywhere in the app → opens tool's platform page
2. Click setup requirements → goes to signup or API key page
3. Copy config snippets, connection strings, or template values directly from the blueprint
4. Goal: never leave Autumn to go search for something — every outbound link is already there

## Data Model

### Existing Tables (Unchanged)

- `workflows` — individual video-extracted blueprints (title, slug, overview, use_case, skill_level, complexity, value_score, etc.)
- `tools` — unique tool names with category, pricing, URL metadata
- `workflow_tools` — junction: workflow ↔ tool
- `workflow_steps` — ordered steps per workflow (step_order, tool_id, action, config, description)
- `workflow_nodes` — node topology per workflow (role, tool_id, config)
- `node_connections` — connections between nodes (source_node_id, target_node_id, data_description)
- `workflow_auth_reqs` — per-tool auth requirements (API key, OAuth, paid plan, free signup)
- `workflow_cost_breakdown` — per-tool pricing and monthly estimates
- `workflow_timestamps` — video chapter timestamps
- `workflow_tags` — categorization tags
- `processed_videos` — videos already processed by the pipeline
- `scan_metadata`, `scan_history` — pipeline run tracking

### Modified Tables

- `user_tools` — stays, gets better UI surfacing with "have / haven't used" split
- `user_workflow_status` — simplified; replaced by `saved_workflows` for most use cases

### New Tables

```
canonical_workflows
  - id INTEGER PRIMARY KEY
  - title TEXT
  - description TEXT
  - use_case TEXT
  - complexity TEXT
  - created_at TIMESTAMP
  - updated_at TIMESTAMP

canonical_sources
  - id INTEGER PRIMARY KEY
  - canonical_workflow_id INTEGER → canonical_workflows.id
  - workflow_id INTEGER → workflows.id
  - added_at TIMESTAMP

canonical_steps
  - id INTEGER PRIMARY KEY
  - canonical_workflow_id INTEGER → canonical_workflows.id
  - step_order INTEGER
  - tool_id INTEGER → tools.id
  - action TEXT
  - config TEXT
  - description TEXT
  - input_description TEXT
  - output_description TEXT

decision_points
  - id INTEGER PRIMARY KEY
  - canonical_step_id INTEGER → canonical_steps.id
  - alternative_tool_id INTEGER → tools.id
  - alternative_action TEXT
  - source_workflow_id INTEGER → workflows.id
  - reasoning TEXT

saved_workflows
  - id INTEGER PRIMARY KEY
  - workflow_id INTEGER → workflows.id (nullable)
  - canonical_workflow_id INTEGER → canonical_workflows.id (nullable)
  - notes TEXT
  - saved_at TIMESTAMP
```

### Pipeline Addition

After extraction, the pipeline auto-detects if a new workflow overlaps with existing canonical workflows:
- **Match found:** Link new workflow as a canonical source, re-synthesize the canonical with any new info or decision points
- **No match:** Workflow lives as standalone; periodically check if multiple standalones should form a new canonical

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3 + Flask |
| Database | SQLite (WAL mode) |
| Frontend | React + TypeScript + Vite |
| Styling | Tailwind CSS |
| Pipeline Visuals | Pure CSS/SVG |
| LLM | Claude Sonnet 4.5 + Haiku 4.5 (direct API) |
| Fonts | Cormorant, DM Sans, IBM Plex Mono |
| Hosting | Local Mac Mini (localhost:5050) |

## UI Direction

Linear's spatial clarity — minimal chrome, generous whitespace, content-forward — warmed up with Autumn's near-black/cream/ember palette, Cormorant serif wordmark, and heavier grain texture throughout. Fixed narrow sidebar (icon + label) for navigation. Wide breathing content area. Detail pages lead with full-width pipeline visualizations. Feels like a curated field guide: visual enough to browse, structured enough to build from.

### Brand Tokens

- **Background:** #0C0C0C (near-black)
- **Text:** #E8E4DF (warm cream)
- **Accents:** Ember, flame, amber tones
- **Grain:** SVG noise filter, heavier than v1
- **Tool colors:** 24 predefined + deterministic warm-hue fallback (15-55 range)
- **Tool icons:** 6 category SVGs (AI, code, automation, git, API, web)

## Build Milestones

### Phase 1: Frontend Scaffold
Set up React + TypeScript + Vite project in `/frontend`. Tailwind config with Autumn color palette, fonts, and grain texture. Sidebar navigation shell with placeholder pages. Vite proxy to Flask API on :5050. Verify: app loads, sidebar navigates between empty pages, brand looks right.

### Phase 2: Workflow List View
Build workflow list/card components. Pull from existing API endpoints. Each card shows reworked title, one-line description, tool icons, and mini pipeline preview. Search and filter controls. Verify: all existing workflows render, filtering works, cards are scannable.

### Phase 3: Detail Page — Pipeline Visualization
Build left-to-right CSS/SVG pipeline diagram from workflow nodes/steps data. Clickable nodes that expand to show tool details and link to platforms. Decision points visually called out. Verify: pick 2-3 workflows, confirm pipeline renders correctly and links work.

### Phase 4: Detail Page — Implementation Content
Below pipeline: step-by-step implementation guide, tool requirements with direct links, cost breakdown, auth requirements inline. The "jump off and do" experience. Verify: every tool links out, every step is actionable, nothing reads as AI filler.

### Phase 5: Canonical Workflows + Save System
New database tables + API endpoints. Pipeline upgrade to auto-detect overlaps and generate canonical workflows. Save/collect functionality with notes. Decision points from merged sources. Verify: run a scan, confirm canonical detection works, save a workflow with notes.

### Phase 6: Content Quality Pass
Tune Claude extraction prompts for better titles, descriptions, and summaries. Re-process existing workflows with improved prompts. Verify: before/after comparison on 5 workflows — new text is specific, human, tells you what the workflow does for you.

### Phase 7: Home Feed + Polish
Build home feed mixing recent, high-value, and canonical workflows. Tools view with "have / haven't used" split. Responsive polish, loading states, error handling, edge cases. Verify: open Autumn cold and the home feed makes you want to click something.
