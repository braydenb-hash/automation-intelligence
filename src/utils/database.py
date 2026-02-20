"""
SQLite database layer for automation-intelligence.
Replaces JSON file reads/writes with relational queries.
"""

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .config import DATA_DIR
from .logger import setup_logger

logger = setup_logger("database")

DB_PATH = DATA_DIR / "automation_intelligence.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    published TEXT,
    use_case TEXT NOT NULL DEFAULT 'general',
    skill_level TEXT NOT NULL DEFAULT 'intermediate',
    overview TEXT DEFAULT '',
    cost_estimate TEXT DEFAULT '',
    complexity TEXT DEFAULT 'Medium',
    value_score INTEGER DEFAULT 0,
    doc_path TEXT DEFAULT '',
    processed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_workflows_use_case ON workflows(use_case);
CREATE INDEX IF NOT EXISTS idx_workflows_skill_level ON workflows(skill_level);
CREATE INDEX IF NOT EXISTS idx_workflows_value_score ON workflows(value_score DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_published ON workflows(published DESC);

CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS workflow_tools (
    workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    tool_id INTEGER NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    PRIMARY KEY (workflow_id, tool_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_tools_tool_id ON workflow_tools(tool_id);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    action TEXT NOT NULL DEFAULT '',
    tool TEXT NOT NULL DEFAULT '',
    details TEXT DEFAULT '',
    UNIQUE(workflow_id, step_number)
);

CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);

CREATE TABLE IF NOT EXISTS workflow_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_workflow_tags_wf_kind ON workflow_tags(workflow_id, kind);

CREATE TABLE IF NOT EXISTS processed_videos (
    video_id TEXT PRIMARY KEY,
    processed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scan_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


# ─── Connection Management ────────────────────────────────────────

def get_connection():
    # type: () -> sqlite3.Connection
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    # type: () -> None
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.close()
    init_scan_history_table()
    logger.info("Database initialized at %s", DB_PATH)


# ─── Slug Helper ──────────────────────────────────────────────────

def _slugify(text):
    # type: (str) -> str
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80]


# ─── Internal Hydration ──────────────────────────────────────────

def _hydrate_workflow(conn, row):
    # type: (sqlite3.Connection, sqlite3.Row) -> Dict[str, Any]
    wf = dict(row)
    workflow_id = wf.pop("id")

    # Tools
    tools_rows = conn.execute(
        "SELECT t.name FROM workflow_tools wt "
        "JOIN tools t ON t.id = wt.tool_id "
        "WHERE wt.workflow_id = ?",
        (workflow_id,),
    ).fetchall()
    wf["tools"] = [r["name"] for r in tools_rows]

    # Steps
    steps_rows = conn.execute(
        "SELECT step_number, action, tool, details FROM workflow_steps "
        "WHERE workflow_id = ? ORDER BY step_number",
        (workflow_id,),
    ).fetchall()
    wf["workflow_steps"] = [
        {"step": r["step_number"], "action": r["action"],
         "tool": r["tool"], "details": r["details"]}
        for r in steps_rows
    ]

    # Tags
    tags_rows = conn.execute(
        "SELECT kind, value FROM workflow_tags "
        "WHERE workflow_id = ? ORDER BY kind, sort_order",
        (workflow_id,),
    ).fetchall()
    tag_map = {
        "when_to_use": [], "when_not_to_use": [],
        "alternatives": [], "pattern_tags": [],
    }
    for r in tags_rows:
        if r["kind"] in tag_map:
            tag_map[r["kind"]].append(r["value"])
    wf.update(tag_map)

    return wf


def _hydrate_workflows(conn, rows):
    # type: (sqlite3.Connection, list) -> List[Dict[str, Any]]
    if not rows:
        return []

    workflow_ids = [r["id"] for r in rows]
    id_set = set(workflow_ids)

    # Batch load tools
    placeholders = ",".join("?" * len(workflow_ids))
    tools_rows = conn.execute(
        "SELECT wt.workflow_id, t.name FROM workflow_tools wt "
        "JOIN tools t ON t.id = wt.tool_id "
        "WHERE wt.workflow_id IN (%s)" % placeholders,
        workflow_ids,
    ).fetchall()
    tools_map = {}  # type: Dict[int, List[str]]
    for r in tools_rows:
        tools_map.setdefault(r["workflow_id"], []).append(r["name"])

    # Batch load steps
    steps_rows = conn.execute(
        "SELECT workflow_id, step_number, action, tool, details FROM workflow_steps "
        "WHERE workflow_id IN (%s) ORDER BY workflow_id, step_number" % placeholders,
        workflow_ids,
    ).fetchall()
    steps_map = {}  # type: Dict[int, list]
    for r in steps_rows:
        steps_map.setdefault(r["workflow_id"], []).append({
            "step": r["step_number"], "action": r["action"],
            "tool": r["tool"], "details": r["details"],
        })

    # Batch load tags
    tags_rows = conn.execute(
        "SELECT workflow_id, kind, value FROM workflow_tags "
        "WHERE workflow_id IN (%s) ORDER BY workflow_id, kind, sort_order" % placeholders,
        workflow_ids,
    ).fetchall()
    tags_map = {}  # type: Dict[int, Dict[str, list]]
    for r in tags_rows:
        wf_tags = tags_map.setdefault(r["workflow_id"], {
            "when_to_use": [], "when_not_to_use": [],
            "alternatives": [], "pattern_tags": [],
        })
        if r["kind"] in wf_tags:
            wf_tags[r["kind"]].append(r["value"])

    # Assemble
    results = []
    for row in rows:
        wf = dict(row)
        wid = wf.pop("id")
        wf["tools"] = tools_map.get(wid, [])
        wf["workflow_steps"] = steps_map.get(wid, [])
        wf.update(tags_map.get(wid, {
            "when_to_use": [], "when_not_to_use": [],
            "alternatives": [], "pattern_tags": [],
        }))
        results.append(wf)

    return results


# ─── Workflow Read Operations ─────────────────────────────────────

def get_all_workflows(use_case=None, skill_level=None, sort_by="value_score",
                      min_value_score=None, published_after=None):
    # type: (Optional[str], Optional[str], str, Optional[int], Optional[str]) -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        query = "SELECT * FROM workflows WHERE 1=1"
        params = []  # type: list

        if use_case:
            query += " AND use_case = ?"
            params.append(use_case)
        if skill_level:
            query += " AND skill_level = ?"
            params.append(skill_level)
        if min_value_score is not None:
            query += " AND value_score >= ?"
            params.append(min_value_score)
        if published_after:
            query += " AND published >= ?"
            params.append(published_after)

        sort_map = {
            "value_score": "value_score DESC",
            "date": "published DESC",
            "title": "LOWER(source_title) ASC",
        }
        query += " ORDER BY " + sort_map.get(sort_by, "value_score DESC")

        rows = conn.execute(query, params).fetchall()
        return _hydrate_workflows(conn, rows)
    finally:
        conn.close()


def get_workflow_by_slug(slug):
    # type: (str) -> Optional[Dict[str, Any]]
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM workflows WHERE slug = ?", (slug,)
        ).fetchone()
        if not row:
            return None
        return _hydrate_workflow(conn, row)
    finally:
        conn.close()


def get_high_value_workflows(threshold=8, limit=6):
    # type: (int, int) -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM workflows WHERE value_score >= ? "
            "ORDER BY value_score DESC, published DESC LIMIT ?",
            (threshold, limit),
        ).fetchall()
        return _hydrate_workflows(conn, rows)
    finally:
        conn.close()


def get_recent_workflows(days=7, limit=5):
    # type: (int, int) -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT * FROM workflows WHERE published >= ? "
            "ORDER BY published DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()
        return _hydrate_workflows(conn, rows)
    finally:
        conn.close()


def get_use_case_summary():
    # type: () -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT use_case, COUNT(*) as count FROM workflows GROUP BY use_case ORDER BY use_case"
        ).fetchall()

        result = []
        for r in rows:
            uc = r["use_case"]
            count = r["count"]
            # Get top workflow for this use case
            top = conn.execute(
                "SELECT slug, source_title, value_score FROM workflows "
                "WHERE use_case = ? ORDER BY value_score DESC LIMIT 1",
                (uc,),
            ).fetchone()
            top_wf = None
            if top:
                top_wf = {
                    "slug": top["slug"],
                    "title": top["source_title"],
                    "value_score": top["value_score"],
                }
            result.append({
                "use_case": uc,
                "count": count,
                "top_workflow": top_wf,
            })
        return result
    finally:
        conn.close()


def get_tool_usage_counts(limit=8):
    # type: (int) -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT t.name, COUNT(*) as count FROM workflow_tools wt "
            "JOIN tools t ON t.id = wt.tool_id "
            "GROUP BY t.id ORDER BY count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"name": r["name"], "count": r["count"]} for r in rows]
    finally:
        conn.close()


def get_stats():
    # type: () -> Dict[str, Any]
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM workflows").fetchone()["c"]

        by_level = {}
        for r in conn.execute(
            "SELECT skill_level, COUNT(*) as c FROM workflows GROUP BY skill_level"
        ).fetchall():
            by_level[r["skill_level"]] = r["c"]

        by_use_case = {}
        for r in conn.execute(
            "SELECT use_case, COUNT(*) as c FROM workflows GROUP BY use_case"
        ).fetchall():
            by_use_case[r["use_case"]] = r["c"]

        high_value = conn.execute(
            "SELECT COUNT(*) as c FROM workflows WHERE value_score >= 8"
        ).fetchone()["c"]

        return {
            "total_workflows": total,
            "by_level": by_level,
            "by_use_case": by_use_case,
            "high_value_count": high_value,
        }
    finally:
        conn.close()


def get_tools_index():
    # type: () -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        tools_rows = conn.execute(
            "SELECT t.id, t.name, COUNT(wt.workflow_id) as workflow_count "
            "FROM tools t "
            "JOIN workflow_tools wt ON wt.tool_id = t.id "
            "GROUP BY t.id ORDER BY workflow_count DESC"
        ).fetchall()

        result = []
        for t in tools_rows:
            wf_rows = conn.execute(
                "SELECT w.slug, w.source_title, w.value_score, w.skill_level "
                "FROM workflows w "
                "JOIN workflow_tools wt ON wt.workflow_id = w.id "
                "WHERE wt.tool_id = ? ORDER BY w.value_score DESC",
                (t["id"],),
            ).fetchall()
            result.append({
                "name": t["name"],
                "workflow_count": t["workflow_count"],
                "workflows": [
                    {
                        "slug": w["slug"],
                        "source_title": w["source_title"],
                        "value_score": w["value_score"],
                        "skill_level": w["skill_level"],
                    }
                    for w in wf_rows
                ],
            })
        return result
    finally:
        conn.close()


def get_workflow_count():
    # type: () -> int
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) as c FROM workflows").fetchone()["c"]
    finally:
        conn.close()


def get_high_value_count(threshold=8):
    # type: (int) -> int
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) as c FROM workflows WHERE value_score >= ?",
            (threshold,),
        ).fetchone()["c"]
    finally:
        conn.close()


# ─── Workflow Write Operations ────────────────────────────────────

def insert_workflow(workflow_dict):
    # type: (Dict[str, Any]) -> int
    conn = get_connection()
    try:
        slug = _slugify(workflow_dict.get("source_title", "untitled"))

        # Handle slug collision
        base_slug = slug
        suffix = 1
        while True:
            existing = conn.execute(
                "SELECT id FROM workflows WHERE slug = ?", (slug,)
            ).fetchone()
            if not existing:
                break
            suffix += 1
            slug = "%s-%d" % (base_slug, suffix)

        with conn:
            conn.execute(
                "INSERT INTO workflows "
                "(slug, source_url, source_title, channel_name, published, "
                "use_case, skill_level, overview, cost_estimate, complexity, "
                "value_score, doc_path, processed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    slug,
                    workflow_dict.get("source_url", ""),
                    workflow_dict.get("source_title", ""),
                    workflow_dict.get("channel_name", ""),
                    workflow_dict.get("published", ""),
                    workflow_dict.get("use_case", "general"),
                    workflow_dict.get("skill_level", "intermediate"),
                    workflow_dict.get("overview", ""),
                    workflow_dict.get("cost_estimate", ""),
                    workflow_dict.get("complexity", "Medium"),
                    workflow_dict.get("value_score", 0),
                    workflow_dict.get("doc_path", ""),
                    workflow_dict.get("processed_at", ""),
                ),
            )

            workflow_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Tools
            for tool_name in workflow_dict.get("tools", []):
                conn.execute(
                    "INSERT OR IGNORE INTO tools(name) VALUES (?)", (tool_name,)
                )
                tool_row = conn.execute(
                    "SELECT id FROM tools WHERE name = ?", (tool_name,)
                ).fetchone()
                conn.execute(
                    "INSERT OR IGNORE INTO workflow_tools(workflow_id, tool_id) VALUES (?, ?)",
                    (workflow_id, tool_row["id"]),
                )

            # Steps
            for step in workflow_dict.get("workflow_steps", []):
                conn.execute(
                    "INSERT INTO workflow_steps(workflow_id, step_number, action, tool, details) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        workflow_id,
                        step.get("step", 0),
                        step.get("action", ""),
                        step.get("tool", ""),
                        step.get("details", ""),
                    ),
                )

            # Tags
            for kind in ("when_to_use", "when_not_to_use", "alternatives", "pattern_tags"):
                for i, value in enumerate(workflow_dict.get(kind, [])):
                    conn.execute(
                        "INSERT INTO workflow_tags(workflow_id, kind, value, sort_order) "
                        "VALUES (?, ?, ?, ?)",
                        (workflow_id, kind, value, i),
                    )

        logger.info("Inserted workflow: %s (id=%d)", slug, workflow_id)
        return workflow_id
    finally:
        conn.close()


def workflow_exists(source_url):
    # type: (str) -> bool
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM workflows WHERE source_url = ?", (source_url,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


# ─── Processed Videos ────────────────────────────────────────────

def get_processed_video_ids():
    # type: () -> set
    conn = get_connection()
    try:
        rows = conn.execute("SELECT video_id FROM processed_videos").fetchall()
        return {r["video_id"] for r in rows}
    finally:
        conn.close()


def add_processed_video_id(video_id):
    # type: (str) -> None
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO processed_videos(video_id) VALUES (?)",
                (video_id,),
            )
    finally:
        conn.close()


def get_processed_video_count():
    # type: () -> int
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) as c FROM processed_videos"
        ).fetchone()["c"]
    finally:
        conn.close()


# ─── Scan Metadata ────────────────────────────────────────────────

def get_last_scan_time():
    # type: () -> Optional[str]
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT value FROM scan_metadata WHERE key = 'last_check'"
        ).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def set_last_scan_time(iso_timestamp):
    # type: (str) -> None
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO scan_metadata(key, value) VALUES ('last_check', ?)",
                (iso_timestamp,),
            )
    finally:
        conn.close()


# ─── Channel Stats ────────────────────────────────────────────────

def get_channel_stats():
    # type: () -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT channel_name, COUNT(*) as total, "
            "ROUND(AVG(value_score), 1) as avg_score, "
            "MAX(value_score) as best_score "
            "FROM workflows GROUP BY channel_name ORDER BY avg_score DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_workflow_count_by_channel():
    # type: () -> Dict[str, int]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT channel_name, COUNT(*) as count FROM workflows GROUP BY channel_name"
        ).fetchall()
        return {r["channel_name"]: r["count"] for r in rows}
    finally:
        conn.close()


# ─── Tool Ecosystem ────────────────────────────────────────────────

def get_tool_pairs():
    # type: () -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT t1.name as tool_a, t2.name as tool_b, COUNT(*) as pair_count "
            "FROM workflow_tools wt1 "
            "JOIN workflow_tools wt2 ON wt1.workflow_id = wt2.workflow_id AND wt1.tool_id < wt2.tool_id "
            "JOIN tools t1 ON t1.id = wt1.tool_id "
            "JOIN tools t2 ON t2.id = wt2.tool_id "
            "GROUP BY t1.name, t2.name "
            "HAVING COUNT(*) >= 2 "
            "ORDER BY pair_count DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─── Scan History ────────────────────────────────────────────────

def init_scan_history_table():
    # type: () -> None
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS scan_history ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "scan_date TEXT NOT NULL, "
                "videos_checked INTEGER DEFAULT 0, "
                "relevant_found INTEGER DEFAULT 0, "
                "workflows_generated INTEGER DEFAULT 0, "
                "completed_at TEXT DEFAULT (datetime('now')))"
            )
    finally:
        conn.close()


def record_scan_result(scan_date, videos_checked, relevant_found, workflows_generated):
    # type: (str, int, int, int) -> None
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO scan_history (scan_date, videos_checked, relevant_found, workflows_generated) "
                "VALUES (?, ?, ?, ?)",
                (scan_date, videos_checked, relevant_found, workflows_generated),
            )
    finally:
        conn.close()


def get_scan_history(limit=10):
    # type: (int) -> List[Dict[str, Any]]
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM scan_history ORDER BY completed_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
