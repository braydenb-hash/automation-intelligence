import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any

from ..utils.config import CURRICULUM_DIR, WORKFLOWS_DIR
from ..utils.database import get_all_workflows
from ..utils.file_manager import write_markdown
from ..utils.logger import setup_logger

logger = setup_logger("curriculum_builder")

LEVEL_ORDER = ["beginner", "intermediate", "advanced"]
LEVEL_LABELS = {
    "beginner": "Fundamentals",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}
LEVEL_DIRS = {
    "beginner": "01-fundamentals",
    "intermediate": "02-intermediate",
    "advanced": "03-advanced",
}


def _slugify(text):
    # type: (str) -> str
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80]


def _relative_path(workflow):
    # type: (Dict[str, Any]) -> str
    level = workflow.get("skill_level", "intermediate")
    level_dir = LEVEL_DIRS.get(level, "02-intermediate")
    slug = _slugify(workflow.get("source_title", "untitled"))
    return "../workflows/%s/%s.md" % (level_dir, slug)


def build_index(workflows):
    # type: (List[Dict[str, Any]]) -> str
    by_level = defaultdict(list)
    for wf in workflows:
        level = wf.get("skill_level", "intermediate")
        by_level[level].append(wf)

    lines = [
        "# Automation Workflows Curriculum",
        "",
        "**Total Workflows:** %d" % len(workflows),
        "",
        "---",
        "",
    ]

    for level in LEVEL_ORDER:
        wfs = by_level.get(level, [])
        label = LEVEL_LABELS.get(level, level.title())
        lines.append("## %s (%d workflows)" % (label, len(wfs)))
        lines.append("")

        if not wfs:
            lines.append("_(No workflows yet)_")
            lines.append("")
            continue

        wfs.sort(key=lambda w: w.get("value_score", 0), reverse=True)

        lines.append("| Workflow | Use Case | Tools | Value |")
        lines.append("|----------|----------|-------|-------|")

        for wf in wfs:
            title = wf.get("source_title", "Untitled")
            link = _relative_path(wf)
            use_case = wf.get("use_case", "general").replace("-", " ").title()
            tools = ", ".join(wf.get("tools", [])[:3])
            score = wf.get("value_score", 0)
            lines.append("| [%s](%s) | %s | %s | %d/10 |" % (
                title, link, use_case, tools, score
            ))

        lines.append("")

    return "\n".join(lines)


def build_learning_paths(workflows):
    # type: (List[Dict[str, Any]]) -> str
    by_use_case = defaultdict(list)
    for wf in workflows:
        uc = wf.get("use_case", "general")
        by_use_case[uc].append(wf)

    lines = [
        "# Learning Paths",
        "",
        "Suggested sequences for learning automation workflows.",
        "",
        "---",
        "",
    ]

    level_rank = {"beginner": 0, "intermediate": 1, "advanced": 2}

    for use_case, wfs in sorted(by_use_case.items()):
        uc_title = use_case.replace("-", " ").title()
        lines.append("## %s" % uc_title)
        lines.append("")

        wfs.sort(key=lambda w: (
            level_rank.get(w.get("skill_level", "intermediate"), 1),
            -w.get("value_score", 0),
        ))

        for i, wf in enumerate(wfs, 1):
            title = wf.get("source_title", "Untitled")
            link = _relative_path(wf)
            level = wf.get("skill_level", "intermediate").title()
            lines.append("%d. [%s](%s) (%s)" % (i, title, link, level))

        lines.append("")

    return "\n".join(lines)


def rebuild_curriculum():
    # type: () -> None
    workflows = get_all_workflows()
    logger.info("Building curriculum from %d workflows", len(workflows))

    index_content = build_index(workflows)
    write_markdown(CURRICULUM_DIR / "INDEX.md", index_content)

    paths_content = build_learning_paths(workflows)
    write_markdown(CURRICULUM_DIR / "learning-paths.md", paths_content)

    logger.info("Curriculum rebuilt successfully")
