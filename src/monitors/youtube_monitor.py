import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from ..utils.config import load_sources, get_youtube_channels, get_filter_keywords, DATA_DIR
from ..utils.file_manager import load_processed_content, save_processed_content
from ..utils.logger import setup_logger

logger = setup_logger("youtube_monitor")

YTDLP_PATH = "/opt/homebrew/bin/yt-dlp"
RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


@dataclass
class VideoInfo:
    video_id: str
    title: str
    channel_name: str
    channel_id: str
    published: str
    url: str
    transcript: str = ""
    is_relevant: bool = False


def fetch_channel_feed(channel_id):
    # type: (str) -> List[Dict[str, str]]
    feed_url = RSS_TEMPLATE.format(channel_id=channel_id)
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read().decode("utf-8")
    except Exception as e:
        logger.error("Failed to fetch feed for %s: %s", channel_id, e)
        return []

    root = ET.fromstring(xml_data)
    entries = []

    for entry in root.findall("atom:entry", ATOM_NS):
        vid_id = entry.find("yt:videoId", ATOM_NS)
        title = entry.find("atom:title", ATOM_NS)
        published = entry.find("atom:published", ATOM_NS)

        if vid_id is not None and title is not None:
            entries.append({
                "video_id": vid_id.text,
                "title": title.text,
                "published": published.text if published is not None else "",
                "url": "https://www.youtube.com/watch?v=%s" % vid_id.text,
            })

    return entries


def extract_transcript(video_id):
    # type: (str) -> Optional[str]
    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "transcript")
        cmd = [
            YTDLP_PATH,
            "--skip-download",
            "--write-auto-sub",
            "--sub-lang", "en",
            "--sub-format", "json3",
            "--no-write-thumbnail",
            "-o", output_template,
            "https://www.youtube.com/watch?v=%s" % video_id,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
        except subprocess.TimeoutExpired:
            logger.warning("Transcript extraction timed out for %s", video_id)
            return None

        # Find the output file
        json3_path = os.path.join(tmpdir, "transcript.en.json3")
        if not os.path.exists(json3_path):
            logger.warning("No transcript file for %s (no English subs?)", video_id)
            return None

        return _parse_json3_transcript(json3_path)


def _parse_json3_transcript(filepath):
    # type: (str) -> str
    with open(filepath, "r") as f:
        data = json.load(f)

    segments = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            text = seg.get("utf8", "").strip()
            if text and text != "\n":
                segments.append(text)

    raw_text = " ".join(segments)
    raw_text = re.sub(r"\[.*?\]", "", raw_text)
    raw_text = re.sub(r"\s+", " ", raw_text).strip()
    return raw_text


def is_relevant(title, transcript, keywords):
    # type: (str, str, List[str]) -> bool
    title_lower = title.lower()
    transcript_prefix = transcript[:500].lower() if transcript else ""
    combined = title_lower + " " + transcript_prefix

    for kw in keywords:
        if kw.lower() in combined:
            return True
    return False


def check_for_new_videos(days_back=7, max_per_channel=3):
    # type: (int, int) -> List[VideoInfo]
    channels = get_youtube_channels()
    keywords = get_filter_keywords()
    processed = load_processed_content()
    processed_ids = set(processed.get("processed_video_ids", []))
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    new_videos = []

    for channel in channels:
        ch_name = channel["name"]
        ch_id = channel["channel_id"]
        logger.info("Checking channel: %s (%s)", ch_name, ch_id)

        entries = fetch_channel_feed(ch_id)
        count = 0

        for entry in entries:
            vid_id = entry["video_id"]

            if vid_id in processed_ids:
                continue

            # Skip if too old
            try:
                pub_str = entry["published"].replace("Z", "+00:00")
                pub_date = datetime.fromisoformat(pub_str).replace(tzinfo=None)
                if pub_date < cutoff:
                    continue
            except (ValueError, AttributeError):
                pass

            if count >= max_per_channel:
                break

            logger.info("  Extracting transcript: %s", entry["title"])
            transcript = extract_transcript(vid_id) or ""

            relevant = is_relevant(entry["title"], transcript, keywords)

            video = VideoInfo(
                video_id=vid_id,
                title=entry["title"],
                channel_name=ch_name,
                channel_id=ch_id,
                published=entry["published"],
                url=entry["url"],
                transcript=transcript,
                is_relevant=relevant,
            )

            new_videos.append(video)
            processed_ids.add(vid_id)
            count += 1

    # Update processed content
    processed["processed_video_ids"] = list(processed_ids)
    processed["last_check"] = datetime.utcnow().isoformat()
    save_processed_content(processed)

    relevant_count = sum(1 for v in new_videos if v.is_relevant)
    logger.info(
        "Found %d new videos (%d relevant) across %d channels",
        len(new_videos), relevant_count, len(channels)
    )

    return new_videos
