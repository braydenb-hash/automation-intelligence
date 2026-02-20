import re
from typing import List, Dict, Any

from ..utils.logger import setup_logger

logger = setup_logger("diagram_generator")


def _sanitize_label(text):
    # type: (str) -> str
    text = re.sub(r'["|{}]', '', text)
    if len(text) > 60:
        text = text[:57] + "..."
    return text


def generate_flowchart(steps, title=""):
    # type: (List[Dict[str, Any]], str) -> str
    if not steps:
        return ""

    lines = ["graph LR"]

    for i, step in enumerate(steps):
        node_id = chr(65 + i) if i < 26 else "N%d" % i
        tool = _sanitize_label(step.get("tool", "Step"))
        action = _sanitize_label(step.get("action", "Step %d" % step.get("step", i + 1)))
        label = "%s: %s" % (tool, action) if tool else action

        if i == 0:
            lines.append("    %s[%s]" % (node_id, label))
        else:
            prev_id = chr(65 + i - 1) if (i - 1) < 26 else "N%d" % (i - 1)
            lines.append("    %s --> %s[%s]" % (prev_id, node_id, label))

    return "\n".join(lines)


def generate_tool_diagram(tools):
    # type: (List[str]) -> str
    if not tools:
        return ""

    lines = ["graph TD"]
    lines.append("    Hub((Workflow))")

    for i, tool in enumerate(tools):
        node_id = "T%d" % i
        safe_name = _sanitize_label(tool)
        lines.append("    Hub --> %s[%s]" % (node_id, safe_name))

    return "\n".join(lines)
