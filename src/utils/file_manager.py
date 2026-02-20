import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from .config import DATA_DIR, DISCOVERIES_DIR
from .logger import setup_logger

logger = setup_logger("file_manager")


def load_json(filepath):
    # type: (Path) -> Any
    if not filepath.exists():
        return {}
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filepath, data):
    # type: (Path, Any) -> None
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.debug("Saved %s", filepath)


# DEPRECATED: Use database.get_processed_video_ids() / get_last_scan_time() instead
def load_processed_content():
    # type: () -> Dict[str, Any]
    return load_json(DATA_DIR / "processed_content.json")


# DEPRECATED: Use database.add_processed_video_id() / set_last_scan_time() instead
def save_processed_content(data):
    # type: (Dict[str, Any]) -> None
    save_json(DATA_DIR / "processed_content.json", data)


# DEPRECATED: Use database.get_all_workflows() instead
def load_workflow_library():
    # type: () -> List[Dict[str, Any]]
    data = load_json(DATA_DIR / "workflow_library.json")
    if isinstance(data, list):
        return data
    return data.get("workflows", [])


# DEPRECATED: Use database.insert_workflow() instead
def save_workflow_library(workflows):
    # type: (List[Dict[str, Any]]) -> None
    save_json(DATA_DIR / "workflow_library.json", {"workflows": workflows})


def write_markdown(filepath, content):
    # type: (Path, str) -> None
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)
    logger.info("Wrote %s", filepath)


def append_discovery(date_str, entry):
    # type: (str, str) -> None
    filepath = DISCOVERIES_DIR / ("%s.md" % date_str)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not filepath.exists():
        header = "# Discoveries - %s\n\n" % date_str
        with open(filepath, "w") as f:
            f.write(header)

    with open(filepath, "a") as f:
        f.write(entry + "\n\n")


def today_str():
    # type: () -> str
    return datetime.now().strftime("%Y-%m-%d")
