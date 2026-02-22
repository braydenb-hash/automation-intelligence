# Autumn v2 — Automation Intelligence

AI-powered workflow library that extracts structured blueprints from YouTube automation content and presents them as interactive, browsable guides.

## Tech Stack

- **Backend:** Python 3 + Flask (existing, extended with new endpoints)
- **Database:** SQLite WAL mode (existing schema + new canonical/save tables)
- **Frontend:** React + TypeScript + Vite (full rebuild from vanilla SPA)
- **Styling:** Tailwind CSS with custom Autumn palette
- **Pipeline Visuals:** Pure CSS/SVG (flexbox cards + SVG arrows, no heavy libraries)
- **LLM:** Claude Sonnet 4.5 (extraction) + Haiku 4.5 (titles) via direct Anthropic API
- **Fonts:** Cormorant (serif wordmark), DM Sans (UI), IBM Plex Mono (data)

## Folder Structure

```
autumn/
├── src/
│   ├── pipeline.py                  # Scan orchestration (existing)
│   ├── monitors/                    # YouTube RSS + transcript extraction (existing)
│   ├── processors/                  # Claude-powered extraction (existing)
│   ├── generators/                  # Markdown/diagram output (existing)
│   ├── dashboard/
│   │   ├── app.py                   # Flask API (existing, extend with new endpoints)
│   │   └── templates/
│   │       └── index.html           # Legacy SPA (keep as fallback, do not modify)
│   └── utils/                       # Database, LLM client, config, logger (existing)
├── frontend/                        # NEW: React + Vite app
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── layout/              # Sidebar, Shell, Navigation
│   │   │   ├── workflows/           # WorkflowCard, WorkflowList, WorkflowDetail
│   │   │   ├── pipeline/            # PipelineView, PipelineNode, PipelineArrow
│   │   │   ├── tools/               # ToolBadge, ToolList, ToolCoverage
│   │   │   └── common/              # Search, Filters, SaveButton, Notes
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Workflows.tsx
│   │   │   ├── WorkflowDetail.tsx
│   │   │   ├── Tools.tsx
│   │   │   └── Saved.tsx
│   │   ├── hooks/                   # useWorkflows, useTools, useSaved, etc.
│   │   ├── api/                     # API client functions
│   │   ├── types/                   # TypeScript interfaces
│   │   └── styles/
│   │       └── tailwind.css
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── config/                          # YAML configs (existing, do not modify)
├── scripts/                         # CLI scripts (existing)
├── docs/
│   └── PRD.md                       # Product requirements
└── output/                          # Generated markdown docs (existing)
```

## Key Commands

```bash
# Backend
python3 -m src.dashboard.app              # Start Flask API on :5050

# Frontend (from /frontend)
npm run dev                                # Vite dev server with hot reload
npm run build                              # Production build
npm run preview                            # Preview production build

# Pipeline
bash scripts/run_daily_scan.sh --days-back 7 --max-per-channel 3
```

## Hard Rules

### Always
- Keep the existing Flask API as the data layer; the React frontend is a consumer of it
- Use Tailwind utility classes for all styling — no inline styles, no CSS modules
- Every tool reference in the UI must link to the tool's platform URL
- Every pipeline node must be clickable and show what goes in / what comes out
- Maintain the Autumn brand: near-black (#0C0C0C), warm cream (#E8E4DF), ember/amber accents
- Use SVG noise filter for grain texture on backgrounds
- Use Cormorant for the wordmark, DM Sans for UI text, IBM Plex Mono for data/code
- Proxy API requests from Vite dev server to Flask backend on :5050

### Never
- Do not modify the existing Python backend code unless adding new endpoints
- Do not modify the legacy index.html SPA
- Do not use heavy visualization libraries (React Flow, D3) — CSS/SVG only for pipelines
- Do not use localStorage or sessionStorage in the React app
- Do not hardcode workflow data — always fetch from the API
- Do not add authentication or multi-user features (out of scope for v2)

## How to Verify Changes

1. Flask API running on :5050, returning JSON for all endpoints
2. Vite dev server proxies to Flask — no CORS issues
3. Workflow list loads and displays all workflows from the database
4. Workflow detail page renders left-to-right pipeline visualization
5. Every tool name in the UI links to its platform URL
6. Saved workflows persist across page refreshes (via API, not localStorage)
7. Brand looks right: dark background, warm text, grain texture, correct fonts

## Gotchas

- The Flask API uses raw SQL via `utils/database.py` — no ORM. New endpoints should follow the same pattern.
- The Anthropic API client (`utils/llm_client.py`) is a direct HTTP client, not the SDK.
- YouTube thumbnails use maxresdefault.jpg with hqdefault.jpg fallback.
- The `tools-database.yaml` has 30+ tools with URLs — use these for outbound links.
- SQLite is in WAL mode — reads don't block writes, but only one writer at a time.
- Vite proxy config needs to forward `/api/*` to `http://localhost:5050`.

## Reference

See @docs/PRD.md for full product requirements, user flows, data model, and build milestones.
