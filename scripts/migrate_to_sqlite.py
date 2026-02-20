#!/usr/bin/env python3
"""
One-time migration: JSON files -> SQLite database.

Usage from project root:
    python scripts/migrate_to_sqlite.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import DATA_DIR
from src.utils.database import (
    init_db, insert_workflow, add_processed_video_id,
    set_last_scan_time, DB_PATH,
)


def migrate():
    print("Migrating to SQLite database at: %s" % DB_PATH)

    if DB_PATH.exists():
        print("ERROR: Database already exists at %s" % DB_PATH)
        print("Delete it first if you want to re-run migration.")
        sys.exit(1)

    # Initialize schema
    init_db()
    print("Schema created.")

    # --- Migrate workflow_library.json ---
    wf_path = DATA_DIR / "workflow_library.json"
    if wf_path.exists():
        with open(wf_path, "r") as f:
            data = json.load(f)

        workflows = data if isinstance(data, list) else data.get("workflows", [])
        print("Found %d workflows to migrate." % len(workflows))

        for i, wf in enumerate(workflows):
            # Normalize workflow_steps
            steps = wf.get("workflow_steps", [])
            normalized = []
            for s in steps:
                normalized.append({
                    "step": s.get("step", 0),
                    "action": s.get("action", ""),
                    "tool": s.get("tool", ""),
                    "details": s.get("details", ""),
                })
            wf["workflow_steps"] = normalized

            insert_workflow(wf)
            print("  [%d/%d] %s" % (i + 1, len(workflows), wf.get("source_title", "Untitled")))

        print("Migrated %d workflows." % len(workflows))
    else:
        print("No workflow_library.json found, skipping.")

    # --- Migrate processed_content.json ---
    pc_path = DATA_DIR / "processed_content.json"
    if pc_path.exists():
        with open(pc_path, "r") as f:
            processed = json.load(f)

        video_ids = processed.get("processed_video_ids", [])
        for vid_id in video_ids:
            add_processed_video_id(vid_id)
        print("Migrated %d processed video IDs." % len(video_ids))

        last_check = processed.get("last_check")
        if last_check:
            set_last_scan_time(last_check)
            print("Migrated last_check: %s" % last_check)
    else:
        print("No processed_content.json found, skipping.")

    print("\nMigration complete!")
    print("Database: %s" % DB_PATH)
    print("\nYou can now rename the old JSON files:")
    print("  mv %s %s.bak" % (wf_path, wf_path))
    print("  mv %s %s.bak" % (pc_path, pc_path))


if __name__ == "__main__":
    migrate()
