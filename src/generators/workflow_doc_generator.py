import re
from pathlib import Path

from ..processors.workflow_analyzer import ExtractedWorkflow
from .diagram_generator import generate_flowchart
from ..utils.config import WORKFLOWS_DIR
from ..utils.file_manager import write_markdown
from ..utils.logger import setup_logger

logger = setup_logger("workflow_doc_generator")

SKILL_EMOJI = {
    "beginner": "⭐",
    "intermediate": "⭐⭐",
    "advanced": "⭐⭐⭐",
}


def _slugify(text):
    # type: (str) -> str
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80]


def _level_dir(skill_level):
    # type: (str) -> str
    mapping = {
        "beginner": "01-fundamentals",
        "intermediate": "02-intermediate",
        "advanced": "03-advanced",
    }
    return mapping.get(skill_level, "02-intermediate")


def generate_workflow_doc(workflow):
    # type: (ExtractedWorkflow) -> Path
    steps_dicts = [
        {"step": s.step, "action": s.action, "tool": s.tool, "details": s.details}
        for s in workflow.workflow_steps
    ]
    flowchart = generate_flowchart(steps_dicts, workflow.source_title)

    tools_section = "\n".join(
        "- **%s**" % tool for tool in workflow.tools
    ) if workflow.tools else "- (none identified)"

    steps_section = "\n".join(
        "%d. **[%s]** %s%s" % (
            s.step, s.tool, s.action,
            "\n   - %s" % s.details if s.details else ""
        )
        for s in workflow.workflow_steps
    ) if workflow.workflow_steps else "_(No steps extracted)_"

    use_section = "\n".join(
        "- %s" % item for item in workflow.when_to_use
    ) if workflow.when_to_use else ""

    not_use_section = "\n".join(
        "- %s" % item for item in workflow.when_not_to_use
    ) if workflow.when_not_to_use else ""

    alt_section = "\n".join(
        "- %s" % item for item in workflow.alternatives
    ) if workflow.alternatives else "_(None identified)_"

    skill_emoji = SKILL_EMOJI.get(workflow.skill_level, "⭐⭐")

    doc = """# {title}

**Use Case:** {use_case}
**Skill Level:** {skill_emoji} {skill_level}
**Estimated Cost:** {cost}
**Complexity:** {complexity}
**Value Score:** {value}/10
**Source:** [{channel}]({url})
**Published:** {published}

## Overview

{overview}

## Tech Stack

{tools}

## Workflow Diagram

```mermaid
{flowchart}
```

## Step-by-Step

{steps}

## When to Use This

{when_use}

{when_not}

## Alternatives

{alternatives}

## Next Steps

- [ ] Test this workflow
- [ ] Customize for your use case
- [ ] Integrate with existing systems
""".format(
        title=workflow.source_title,
        use_case=workflow.use_case.replace("-", " ").title(),
        skill_emoji=skill_emoji,
        skill_level=workflow.skill_level.title(),
        cost=workflow.cost_estimate or "Not estimated",
        complexity=workflow.complexity,
        value=workflow.value_score,
        channel=workflow.channel_name,
        url=workflow.source_url,
        published=workflow.published[:10] if workflow.published else "Unknown",
        overview=workflow.overview or "_(No overview available)_",
        tools=tools_section,
        flowchart=flowchart,
        steps=steps_section,
        when_use=use_section,
        when_not=not_use_section,
        alternatives=alt_section,
    )

    level_dir = _level_dir(workflow.skill_level)
    slug = _slugify(workflow.source_title)
    filepath = WORKFLOWS_DIR / level_dir / ("%s.md" % slug)

    write_markdown(filepath, doc)
    logger.info("Generated doc: %s", filepath)
    return filepath
