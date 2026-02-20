import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(os.path.expanduser("~/automation-intelligence"))
CONFIG_DIR = PROJECT_ROOT / "config"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

OPENCLAW_DIR = Path(os.path.expanduser("~/.openclaw"))
OPENCLAW_WORKSPACE = OPENCLAW_DIR / "workspace"
AUTH_PROFILES_PATH = OPENCLAW_DIR / "agents" / "main" / "agent" / "auth-profiles.json"

WORKFLOWS_DIR = OUTPUT_DIR / "workflows"
DISCOVERIES_DIR = OUTPUT_DIR / "discoveries"
CURRICULUM_DIR = OUTPUT_DIR / "curriculum"
USE_CASES_DIR = OUTPUT_DIR / "use-cases"
TOOLS_DIR = OUTPUT_DIR / "tools"


def load_yaml(filename):
    # type: (str) -> Dict[str, Any]
    filepath = CONFIG_DIR / filename
    with open(filepath, "r") as f:
        return yaml.safe_load(f)


def load_sources():
    # type: () -> Dict[str, Any]
    return load_yaml("sources.yaml")


def load_categories():
    # type: () -> Dict[str, Any]
    return load_yaml("categories.yaml")


def load_tools_database():
    # type: () -> Dict[str, Any]
    return load_yaml("tools-database.yaml")


def get_youtube_channels():
    # type: () -> List[Dict[str, str]]
    sources = load_sources()
    return sources.get("youtube_channels", [])


def get_filter_keywords():
    # type: () -> List[str]
    sources = load_sources()
    return sources.get("filter_keywords", [])


def load_workflow_groups():
    # type: () -> Dict[str, Any]
    return load_yaml("workflow-groups.yaml")
