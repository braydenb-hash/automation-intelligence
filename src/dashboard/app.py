import os
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import markdown
import yaml
from flask import Flask, jsonify, request, render_template

from ..utils.config import (
    DATA_DIR, OUTPUT_DIR, WORKFLOWS_DIR, DISCOVERIES_DIR,
    CURRICULUM_DIR, CONFIG_DIR, PROJECT_ROOT
)
from ..utils.config import load_sources, load_categories, load_tools_database, load_workflow_groups
from ..utils.database import (
    init_db, get_all_workflows, get_workflow_by_slug,
    get_high_value_workflows, get_recent_workflows,
    get_use_case_summary, get_tool_usage_counts,
    get_stats, get_tools_index as db_get_tools_index,
    get_workflow_count, get_high_value_count,
    get_processed_video_count, get_last_scan_time,
    get_channel_stats, get_workflow_count_by_channel,
    get_tool_pairs, get_scan_history,
)

app = Flask(__name__, template_folder=str(PROJECT_ROOT / "src" / "dashboard" / "templates"))

md = markdown.Markdown(extensions=["tables", "fenced_code"])


def _slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80]


# --- Pages ---

@app.route("/")
def index():
    return render_template("index.html")


# --- API ---

@app.route("/api/stats")
def api_stats():
    stats = get_stats()
    stats["last_scan"] = get_last_scan_time()
    stats["videos_processed"] = get_processed_video_count()
    return jsonify(stats)


@app.route("/api/pulse")
def api_pulse():
    """The Pulse — curated high-value overview for the homepage."""
    high_value = get_high_value_workflows(threshold=8, limit=6)
    recent = get_recent_workflows(days=7, limit=5)
    use_cases = get_use_case_summary()
    top_tools = get_tool_usage_counts(limit=8)

    return jsonify({
        "total_workflows": get_workflow_count(),
        "high_value_count": get_high_value_count(threshold=8),
        "high_value": [{
            "slug": w.get("slug", ""),
            "source_title": w.get("source_title", ""),
            "channel_name": w.get("channel_name", ""),
            "value_score": w.get("value_score", 0),
            "skill_level": w.get("skill_level", ""),
            "use_case": w.get("use_case", ""),
            "overview": w.get("overview", ""),
            "tools": w.get("tools", []),
            "published": w.get("published", ""),
            "workflow_steps": w.get("workflow_steps", []),
        } for w in high_value],
        "recent": [{
            "slug": w.get("slug", ""),
            "source_title": w.get("source_title", ""),
            "channel_name": w.get("channel_name", ""),
            "value_score": w.get("value_score", 0),
            "skill_level": w.get("skill_level", ""),
            "published": w.get("published", ""),
        } for w in recent],
        "use_cases": use_cases,
        "top_tools": top_tools,
        "tool_pairs": get_tool_pairs(),
        "last_scan": get_last_scan_time(),
        "videos_processed": get_processed_video_count(),
    })


@app.route("/api/workflows")
def api_workflows():
    use_case = request.args.get("use_case")
    skill_level = request.args.get("skill_level")
    sort_by = request.args.get("sort", "value_score")

    workflows = get_all_workflows(
        use_case=use_case,
        skill_level=skill_level,
        sort_by=sort_by,
    )
    return jsonify(workflows)


@app.route("/api/workflows/<slug>")
def api_workflow_detail(slug):
    workflow = get_workflow_by_slug(slug)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    # Find and render the markdown file
    level_dirs = {
        "beginner": "01-fundamentals",
        "intermediate": "02-intermediate",
        "advanced": "03-advanced",
    }
    level_dir = level_dirs.get(workflow.get("skill_level", "intermediate"), "02-intermediate")
    md_path = WORKFLOWS_DIR / level_dir / ("%s.md" % slug)

    html_content = ""
    if md_path.exists():
        with open(md_path, "r") as f:
            md.reset()
            html_content = md.convert(f.read())

    workflow["html_content"] = html_content
    workflow["slug"] = slug
    return jsonify(workflow)


@app.route("/api/discoveries")
def api_discoveries():
    dates = []
    if DISCOVERIES_DIR.exists():
        for f in sorted(DISCOVERIES_DIR.glob("*.md"), reverse=True):
            dates.append(f.stem)
    return jsonify(dates)


@app.route("/api/discoveries/<date>")
def api_discovery_detail(date):
    filepath = DISCOVERIES_DIR / ("%s.md" % date)
    if not filepath.exists():
        return jsonify({"error": "No discoveries for this date"}), 404

    with open(filepath, "r") as f:
        md.reset()
        html_content = md.convert(f.read())

    return jsonify({"date": date, "html": html_content})


@app.route("/api/sources")
def api_sources():
    sources = load_sources()
    channels = sources.get("youtube_channels", [])
    # Enrich with workflow counts
    counts = get_workflow_count_by_channel()
    for ch in channels:
        ch["workflow_count"] = counts.get(ch.get("name", ""), 0)
    return jsonify(channels)


@app.route("/api/sources", methods=["POST"])
def api_add_source():
    data = request.get_json()
    handle = (data.get("handle") or "").strip()
    if not handle:
        return jsonify({"error": "handle is required"}), 400

    # Normalize handle
    if not handle.startswith("@"):
        handle = "@" + handle

    # Resolve channel ID from handle
    try:
        url = "https://www.youtube.com/%s" % handle
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        match = re.search(r'channel_id=([^"&]+)', html)
        if not match:
            return jsonify({"error": "Could not resolve channel ID for %s" % handle}), 400
        channel_id = match.group(1)
    except Exception as e:
        return jsonify({"error": "Failed to resolve handle: %s" % str(e)}), 400

    # Get channel name from RSS feed
    try:
        feed_url = "https://www.youtube.com/feeds/videos.xml?channel_id=%s" % channel_id
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read().decode("utf-8")
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        title_el = root.find("atom:title", ns)
        channel_name = title_el.text if title_el is not None else handle.lstrip("@")
    except Exception:
        channel_name = handle.lstrip("@")

    # Load current sources and check for duplicates
    sources_path = CONFIG_DIR / "sources.yaml"
    with open(sources_path, "r") as f:
        sources = yaml.safe_load(f)

    channels = sources.get("youtube_channels", [])
    for ch in channels:
        if ch.get("channel_id") == channel_id:
            return jsonify({"error": "Channel already exists: %s" % ch.get("name")}), 409

    # Add new channel
    new_channel = {
        "name": data.get("name") or channel_name,
        "channel_id": channel_id,
        "handle": handle,
        "focus": data.get("focus", ""),
        "priority": data.get("priority", "medium"),
    }
    channels.append(new_channel)
    sources["youtube_channels"] = channels

    with open(sources_path, "w") as f:
        yaml.dump(sources, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return jsonify(new_channel), 201


@app.route("/api/sources/<channel_id>", methods=["DELETE"])
def api_remove_source(channel_id):
    sources_path = CONFIG_DIR / "sources.yaml"
    with open(sources_path, "r") as f:
        sources = yaml.safe_load(f)

    channels = sources.get("youtube_channels", [])
    original_len = len(channels)
    channels = [ch for ch in channels if ch.get("channel_id") != channel_id]

    if len(channels) == original_len:
        return jsonify({"error": "Channel not found"}), 404

    sources["youtube_channels"] = channels
    with open(sources_path, "w") as f:
        yaml.dump(sources, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return jsonify({"status": "removed", "channel_id": channel_id})


def _match_workflows_to_group(workflows, group_def):
    """Match workflows to a consolidation group based on matchers."""
    matchers = group_def.get("matchers", {})
    slug_list = matchers.get("slug_list", [])
    title_keywords = matchers.get("title_keywords", [])
    required_tools = matchers.get("required_tools", [])
    use_case = matchers.get("use_case", "")

    matched = []
    for wf in workflows:
        slug = _slugify(wf.get("source_title", ""))

        # Direct slug match takes priority
        if slug_list and slug in slug_list:
            matched.append(wf)
            continue

        # Keyword + use_case matching
        if not slug_list:
            title_lower = wf.get("source_title", "").lower()
            title_match = any(kw.lower() in title_lower for kw in title_keywords) if title_keywords else True
            tool_match = all(t in wf.get("tools", []) for t in required_tools) if required_tools else True
            uc_match = (wf.get("use_case", "") == use_case) if use_case else True

            if title_match and tool_match and uc_match:
                matched.append(wf)

    return matched


def _merge_workflow_steps(members):
    """Merge workflow steps from multiple workflows, deduplicating similar steps."""
    all_steps = []
    for member in members:
        for step in member.get("workflow_steps", []):
            step_copy = dict(step)
            step_copy["_source"] = member.get("source_title", "")
            all_steps.append(step_copy)

    # Group by tool + similar action
    merged = []
    used = set()
    for i, step in enumerate(all_steps):
        if i in used:
            continue
        cluster = [step]
        for j in range(i + 1, len(all_steps)):
            if j in used:
                continue
            other = all_steps[j]
            if step.get("tool") == other.get("tool") and _word_overlap(step.get("action", ""), other.get("action", "")) > 0.4:
                cluster.append(other)
                used.add(j)

        sources = list(set(c["_source"] for c in cluster))
        merged.append({
            "step": len(merged) + 1,
            "action": cluster[0].get("action", ""),
            "tool": cluster[0].get("tool", ""),
            "details": cluster[0].get("details", ""),
            "sources": sources,
            "is_shared": len(sources) > 1,
            "is_unique": len(sources) == 1,
        })

    return merged


def _word_overlap(a, b):
    """Simple word overlap ratio for fuzzy matching."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


@app.route("/api/workflow-groups")
def api_workflow_groups():
    workflows = get_all_workflows()
    try:
        groups_config = load_workflow_groups()
    except Exception:
        groups_config = {"groups": []}

    groups = []
    grouped_slugs = set()

    for group_def in groups_config.get("groups", []):
        members = _match_workflows_to_group(workflows, group_def)
        if len(members) >= 2:
            all_tools = list(set(t for m in members for t in m.get("tools", [])))
            combined_steps = _merge_workflow_steps(members)

            for m in members:
                m["slug"] = _slugify(m.get("source_title", ""))

            groups.append({
                "id": group_def["id"],
                "name": group_def["name"],
                "description": group_def.get("description", ""),
                "member_count": len(members),
                "members": [{
                    "source_title": m.get("source_title", ""),
                    "channel_name": m.get("channel_name", ""),
                    "skill_level": m.get("skill_level", ""),
                    "value_score": m.get("value_score", 0),
                    "slug": m.get("slug", ""),
                    "source_url": m.get("source_url", ""),
                    "use_case": m.get("use_case", ""),
                } for m in members],
                "combined_tools": all_tools,
                "combined_steps": combined_steps,
                "avg_value_score": round(sum(m.get("value_score", 0) for m in members) / len(members), 1),
                "skill_range": sorted(set(m.get("skill_level", "") for m in members)),
            })
            for m in members:
                grouped_slugs.add(_slugify(m.get("source_title", "")))

    # Ungrouped workflows
    ungrouped = []
    for wf in workflows:
        slug = _slugify(wf.get("source_title", ""))
        if slug not in grouped_slugs:
            wf["slug"] = slug
            ungrouped.append(wf)

    ungrouped.sort(key=lambda w: w.get("value_score", 0), reverse=True)

    return jsonify({"groups": groups, "ungrouped": ungrouped})


@app.route("/api/tools-index")
def api_tools_index():
    tools_data = db_get_tools_index()

    # Enrich with metadata from tools-database.yaml
    try:
        tools_db = load_tools_database()
    except Exception:
        tools_db = {"tools": []}
    tools_lookup = {t["name"]: t for t in tools_db.get("tools", [])}

    result = []
    for tool in tools_data:
        db_info = tools_lookup.get(tool["name"], {})
        result.append({
            "name": tool["name"],
            "category": db_info.get("category", ""),
            "pricing": db_info.get("pricing", ""),
            "url": db_info.get("url", ""),
            "workflow_count": tool["workflow_count"],
            "workflows": tool["workflows"],
        })

    return jsonify(result)


@app.route("/api/channel-stats")
def api_channel_stats():
    stats = get_channel_stats()
    return jsonify(stats)


@app.route("/api/scan-history")
def api_scan_history():
    history = get_scan_history(limit=10)
    return jsonify(history)


@app.route("/api/scan", methods=["POST"])
def api_trigger_scan():
    script = str(PROJECT_ROOT / "scripts" / "run_daily_scan.sh")
    try:
        subprocess.Popen(
            ["bash", script, "--days-back", "7", "--max-per-channel", "3"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(PROJECT_ROOT),
        )
        return jsonify({"status": "started", "message": "Scan started in background"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def create_app():
    init_db()
    return app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
