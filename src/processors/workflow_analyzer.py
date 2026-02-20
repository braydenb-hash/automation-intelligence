import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

from ..utils.llm_client import call_claude
from ..utils.config import load_tools_database
from ..utils.logger import setup_logger

logger = setup_logger("workflow_analyzer")


@dataclass
class WorkflowStep:
    step: int
    action: str
    tool: str
    details: str = ""


@dataclass
class ExtractedWorkflow:
    source_url: str
    source_title: str
    channel_name: str
    published: str
    use_case: str
    skill_level: str
    tools: List[str] = field(default_factory=list)
    workflow_steps: List[WorkflowStep] = field(default_factory=list)
    overview: str = ""
    cost_estimate: str = ""
    complexity: str = ""
    value_score: int = 0
    when_to_use: List[str] = field(default_factory=list)
    when_not_to_use: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    pattern_tags: List[str] = field(default_factory=list)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        return asdict(self)


ANALYSIS_SYSTEM_PROMPT = """You are an AI automation workflow analyst. Your job is to analyze video transcripts about AI tools and automation, then extract structured workflow information.

You must respond with ONLY valid JSON (no markdown fences, no explanation outside the JSON).

Known tools in the ecosystem: {tools_list}

Use case categories: content-pipeline, sales-automation, data-ops, customer-support, development-ops, research-analysis, personal-productivity, general

Skill levels: beginner (no-code), intermediate (some API/scripting), advanced (custom code/agents)"""


ANALYSIS_USER_PROMPT = """Analyze this video transcript and extract any automation workflows described.

Video title: {title}
Channel: {channel}
URL: {url}

Transcript (first 8000 chars):
{transcript}

Respond with a JSON object containing:
{{
  "has_workflow": true/false,
  "use_case": "category-id",
  "skill_level": "beginner|intermediate|advanced",
  "tools": ["Tool1", "Tool2"],
  "overview": "2-3 sentence description of the workflow",
  "workflow_steps": [
    {{"step": 1, "action": "description", "tool": "ToolName", "details": "optional extra details"}}
  ],
  "cost_estimate": "$X/month + $Y per execution",
  "complexity": "Low|Medium|High",
  "value_score": 1-10,
  "when_to_use": ["scenario 1", "scenario 2"],
  "when_not_to_use": ["scenario 1"],
  "alternatives": ["alternative approach 1"],
  "pattern_tags": ["tag1", "tag2", "tag3"]
}}

For "pattern_tags", provide 2-4 short tags describing the core pattern (e.g., "multi-agent", "website-building", "research-automation", "no-code", "voice-agent", "content-pipeline").

If the video does NOT describe a concrete automation workflow (e.g., it's just news or opinion), set "has_workflow": false and leave other fields empty/default."""


def analyze_transcript(title, channel, url, transcript):
    # type: (str, str, str, str) -> Optional[Dict[str, Any]]
    tools_db = load_tools_database()
    tools_list = ", ".join(t["name"] for t in tools_db.get("tools", []))

    system = ANALYSIS_SYSTEM_PROMPT.format(tools_list=tools_list)
    user_msg = ANALYSIS_USER_PROMPT.format(
        title=title,
        channel=channel,
        url=url,
        transcript=transcript[:8000],
    )

    try:
        response_text = call_claude(
            prompt=user_msg,
            system=system,
            temperature=0.2,
            max_tokens=2048,
        )
    except RuntimeError as e:
        logger.error("LLM call failed: %s", e)
        return None

    # Parse JSON response
    try:
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        result = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM response as JSON: %s", e)
        logger.debug("Raw response: %s", response_text[:500])
        return None

    if not result.get("has_workflow", False):
        logger.info("No workflow found in: %s", title)
        return None

    return result


def build_workflow(video_url, video_title, channel_name, published, analysis):
    # type: (str, str, str, str, Dict[str, Any]) -> ExtractedWorkflow
    steps = [
        WorkflowStep(
            step=s.get("step", i + 1),
            action=s.get("action", ""),
            tool=s.get("tool", ""),
            details=s.get("details", ""),
        )
        for i, s in enumerate(analysis.get("workflow_steps", []))
    ]

    return ExtractedWorkflow(
        source_url=video_url,
        source_title=video_title,
        channel_name=channel_name,
        published=published,
        use_case=analysis.get("use_case", "general"),
        skill_level=analysis.get("skill_level", "intermediate"),
        tools=analysis.get("tools", []),
        workflow_steps=steps,
        overview=analysis.get("overview", ""),
        cost_estimate=analysis.get("cost_estimate", ""),
        complexity=analysis.get("complexity", "Medium"),
        value_score=analysis.get("value_score", 5),
        when_to_use=analysis.get("when_to_use", []),
        when_not_to_use=analysis.get("when_not_to_use", []),
        alternatives=analysis.get("alternatives", []),
        pattern_tags=analysis.get("pattern_tags", []),
    )
