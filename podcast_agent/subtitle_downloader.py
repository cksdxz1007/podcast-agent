"""Subtitle downloader module - downloads subtitles using yt-dlp subprocess."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def download_subtitle(
    url: str,
    language: str,
    subtitle_type: str,
    output_dir: Path,
    name: str = "subtitle",
    cookie_file: Path | None = None,
) -> Path:
    """Download subtitle via yt-dlp subprocess, save to output_dir with predictable name.

    Args:
        url: Video URL
        language: Language code (e.g. 'en', 'zh-Hans')
        subtitle_type: 'manual' or 'auto'
        output_dir: Directory to save the subtitle file
        name: Name prefix for the output file
        cookie_file: Optional path to cookies file

    Returns:
        Path to the saved subtitle file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to a temp dir, yt-dlp names the file based on video title
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "yt-dlp",
            "--no-download",
            "--quiet",
            "--no-warnings",
            "--write-subs" if subtitle_type == "manual" else "--write-auto-subs",
            "--sub-langs", language,
            "--sub-lang", "srt",
            "--convert-subs", "srt",
            "-o", tmp + "/%(title)s.%(ext)s",
            url,
        ]

        if cookie_file and cookie_file.exists():
            cmd += ["--cookies", str(cookie_file)]
            logger.info(f"Using cookies from: {cookie_file}")
        else:
            browser = os.environ.get("YOUTUBE_BROWSER", "firefox")
            cmd += ["--cookies-from-browser", browser]
            logger.info(f"Using cookies from browser: {browser}")

        logger.info(f"Downloading {language} {subtitle_type} subtitles via yt-dlp...")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            raise RuntimeError("yt-dlp subtitle download timed out")

        if result.returncode != 0:
            logger.warning(f"yt-dlp subtitle download failed: {result.stderr.strip()}")
            raise RuntimeError(f"Failed to download subtitles: {result.stderr.strip()}")

        # Find the subtitle file in tmp dir
        candidates = list(Path(tmp).glob("*"))
        subtitle_files = [
            f for f in candidates
            if f.is_file() and f.suffix.lower() in (".srt", ".vtt", ".ass", ".ttml")
        ]
        if not subtitle_files:
            raise RuntimeError("Subtitle file was not saved to disk")

        sub = subtitle_files[0]
        final_path = output_dir / f"{name}_subtitle{sub.suffix}"
        sub.rename(final_path)
        logger.info(f"Subtitle saved to: {final_path}")
        return final_path
