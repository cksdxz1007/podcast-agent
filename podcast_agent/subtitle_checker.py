"""Subtitle checker module - uses yt-dlp to check available subtitles."""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SubtitleInfo:
    """Information about an available subtitle track."""
    subtitle_type: str  # "manual" or "auto"
    language_code: str
    download_url: str | None = None


def _detect_chinese(code: str) -> bool:
    return code.lower().startswith("zh")


def _detect_english(code: str) -> bool:
    return code.lower() == "en"


def check_subtitles(url: str, cookie_file: Path | None = None) -> SubtitleInfo | None:
    """Check available subtitles for a URL using yt-dlp --dump-json.

    Args:
        url: Video URL
        cookie_file: Optional path to cookies file

    Returns:
        SubtitleInfo if Chinese or English subtitles are available, None otherwise.

    Priority:
        1. Manual Chinese subtitles > Manual English subtitles
        2. Auto Chinese subtitles > Auto English subtitles
    """
    logger.info(f"Checking subtitles for: {url}")

    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--no-warnings",
        "--quiet",
    ]

    if cookie_file and cookie_file.exists():
        cmd += ["--cookies", str(cookie_file)]
        logger.info(f"Using cookies from: {cookie_file}")
    else:
        browser = os.environ.get("YOUTUBE_BROWSER", "firefox")
        cmd += ["--cookies-from-browser", browser]
        logger.info(f"Using cookies from browser: {browser}")

    try:
        result = subprocess.run(
            cmd + [url],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp --dump-json timed out")
        return None

    if result.returncode != 0:
        logger.warning(f"yt-dlp --dump-json failed: {result.stderr.strip()}")
        return None

    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning(f"yt-dlp --dump-json returned invalid JSON")
        return None

    subtitles: dict = info.get("subtitles") or {}
    auto_captions: dict = info.get("automatic_captions") or {}

    # Priority 1: Manual subtitles
    for lang_code in subtitles:
        if _detect_chinese(lang_code):
            logger.info(f"Found manual subtitle: {lang_code}")
            return SubtitleInfo(subtitle_type="manual", language_code=lang_code)
    for lang_code in subtitles:
        if _detect_english(lang_code):
            logger.info(f"Found manual subtitle: {lang_code}")
            return SubtitleInfo(subtitle_type="manual", language_code=lang_code)

    # Priority 2: Auto-generated subtitles
    for lang_code in auto_captions:
        if _detect_chinese(lang_code):
            logger.info(f"Found auto subtitle: {lang_code}")
            return SubtitleInfo(subtitle_type="auto", language_code=lang_code)
    for lang_code in auto_captions:
        if _detect_english(lang_code):
            logger.info(f"Found auto subtitle: {lang_code}")
            return SubtitleInfo(subtitle_type="auto", language_code=lang_code)

    logger.info("No Chinese or English subtitles available")
    return None


def list_all_subtitles(url: str) -> dict:
    """List all available subtitles (for debugging)."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--no-warnings",
        "--quiet",
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return {}

    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

    return {
        "manual": info.get("subtitles") or {},
        "auto": info.get("automatic_captions") or {},
    }
