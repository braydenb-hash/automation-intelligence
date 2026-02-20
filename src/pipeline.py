import sys
from datetime import datetime
from typing import List, Dict, Any

from .monitors.youtube_monitor import check_for_new_videos, VideoInfo
from .processors.workflow_analyzer import analyze_transcript, build_workflow
from .generators.workflow_doc_generator import generate_workflow_doc
from .generators.curriculum_builder import rebuild_curriculum
from .utils.database import insert_workflow, record_scan_result
from .utils.file_manager import append_discovery, today_str
from .utils.logger import setup_logger

logger = setup_logger("pipeline")


def run_daily_scan(days_back=7, max_per_channel=3):
    # type: (int, int) -> Dict[str, Any]
    logger.info("=== Starting daily scan (%s) ===", today_str())

    # Step 1: Monitor
    logger.info("Step 1: Checking YouTube channels for new videos...")
    new_videos = check_for_new_videos(
        days_back=days_back,
        max_per_channel=max_per_channel,
    )

    relevant_videos = [v for v in new_videos if v.is_relevant]
    logger.info(
        "Found %d relevant videos out of %d new",
        len(relevant_videos), len(new_videos)
    )

    if not relevant_videos:
        logger.info("No relevant videos found. Updating curriculum anyway.")
        rebuild_curriculum()
        return {
            "date": today_str(),
            "videos_checked": len(new_videos),
            "relevant_found": 0,
            "workflows_generated": 0,
            "high_value": [],
        }

    # Step 2: Analyze
    logger.info("Step 2: Analyzing transcripts...")
    workflows_generated = []

    for video in relevant_videos:
        if not video.transcript:
            logger.warning("Skipping %s (no transcript)", video.title)
            continue

        logger.info("  Analyzing: %s", video.title)
        analysis = analyze_transcript(
            title=video.title,
            channel=video.channel_name,
            url=video.url,
            transcript=video.transcript,
        )

        if analysis is None:
            continue

        wf = build_workflow(
            video_url=video.url,
            video_title=video.title,
            channel_name=video.channel_name,
            published=video.published,
            analysis=analysis,
        )

        # Step 3: Generate documentation
        logger.info("  Generating doc for: %s", wf.source_title)
        doc_path = generate_workflow_doc(wf)

        wf_dict = wf.to_dict()
        wf_dict["doc_path"] = str(doc_path)
        wf_dict["processed_at"] = datetime.utcnow().isoformat()
        insert_workflow(wf_dict)
        workflows_generated.append(wf_dict)

        # Log discovery
        discovery_entry = (
            "### %s\n"
            "- **Source:** [%s](%s)\n"
            "- **Use Case:** %s\n"
            "- **Skill Level:** %s\n"
            "- **Value Score:** %d/10\n"
            "- **Tools:** %s\n"
            "- **Doc:** %s\n"
        ) % (
            wf.source_title,
            wf.channel_name, wf.source_url,
            wf.use_case,
            wf.skill_level,
            wf.value_score,
            ", ".join(wf.tools),
            doc_path,
        )
        append_discovery(today_str(), discovery_entry)

    # Step 4: Rebuild curriculum
    logger.info("Step 4: Rebuilding curriculum...")
    rebuild_curriculum()

    high_value = [
        wf for wf in workflows_generated
        if wf.get("value_score", 0) >= 8
    ]

    summary = {
        "date": today_str(),
        "videos_checked": len(new_videos),
        "relevant_found": len(relevant_videos),
        "workflows_generated": len(workflows_generated),
        "high_value": [
            {
                "title": w["source_title"],
                "score": w["value_score"],
                "url": w["source_url"],
            }
            for w in high_value
        ],
    }

    # Record scan history
    record_scan_result(
        scan_date=today_str(),
        videos_checked=len(new_videos),
        relevant_found=len(relevant_videos),
        workflows_generated=len(workflows_generated),
    )

    logger.info(
        "=== Scan complete: %d workflows generated, %d high-value ===",
        len(workflows_generated), len(high_value)
    )

    return summary
