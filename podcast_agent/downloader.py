"""Download module - handles video/audio downloading from various sources."""

import logging
import subprocess
from pathlib import Path

from .config import Config

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Raised when download fails."""
    pass


class Downloader:
    """Downloads audio/video from various sources."""

    def __init__(self, config: Config):
        self.config = config

    def download(self, url: str, name: str = "podcast") -> Path:
        """Download audio from URL and return path to audio file.

        Args:
            url: Source URL (Bilibili, YouTube, or generic). Can contain extra text.
            name: Name for the podcast (used in temp file naming)

        Returns:
            Path to the downloaded audio file (MP3)
        """
        logger.info("Starting download...")

        # Extract clean URL if text contains extra content
        clean_url = self._extract_url(url)
        logger.info(f"Clean URL: {clean_url}")

        if "bilibili.com" in clean_url or "b23.tv" in clean_url:
            return self._download_bilibili(clean_url, name)
        elif "youtube.com" in clean_url or "youtu.be" in clean_url:
            return self._download_youtube(clean_url, name)
        else:
            return self._download_generic(clean_url, name)

    def _extract_url(self, text: str) -> str:
        """Extract URL from text that may contain extra content.

        Handles formats like:
        - 【标题】 https://example.com
        - 链接：https://example.com
        - https://example.com (already clean)
        """
        import re
        # URL pattern
        url_pattern = r'https?://[^\s<>\"\'）】]+'
        match = re.search(url_pattern, text)
        if match:
            return match.group(0)
        return text.strip()

    def _download_bilibili(self, url: str, name: str) -> Path:
        """Download from Bilibili using cookies."""
        cookie_file = self.config.cookie_file
        if not cookie_file.exists():
            raise DownloadError(f"Bilibili cookie file not found: {cookie_file}")

        logger.info("Detected Bilibili video, downloading...")

        # Use project tmp directory
        tmp_dir = self.config.script_dir / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        output_file = tmp_dir / f"video_{name}_{id(self)}.mp4"
        audio_file = tmp_dir / f"audio_{name}_{id(self)}.mp3"

        try:
            # Download with default quality selection
            result = subprocess.run(
                ["yt-dlp", "--cookies", str(cookie_file),
                 "--merge-output-format", "mp4",
                 "-o", str(output_file), url],
                capture_output=True, text=True
            )

            if result.returncode != 0 or not output_file.exists():
                logger.warning(f"Download warning: {result.stderr}")
                # Fallback: try without format selection
                result = subprocess.run(
                    ["yt-dlp", "--cookies", str(cookie_file),
                     "-o", str(output_file), url],
                    capture_output=True, text=True
                )
                if result.returncode != 0 or not output_file.exists():
                    raise DownloadError(f"Bilibili download failed: {result.stderr}")

            # Extract audio
            audio_file = self._extract_audio(output_file, audio_file)
            logger.info("Bilibili download complete")
            return audio_file
        finally:
            # Clean up video file
            if output_file.exists():
                output_file.unlink()

    def _download_youtube(self, url: str, name: str) -> Path:
        """Download from YouTube as MP3."""
        import time
        logger.info("Detected YouTube video, downloading...")

        tmp_dir = self.config.script_dir / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        timestamp = int(time.time() * 1000)
        audio_file = tmp_dir / f"yt_audio_{name}_{timestamp}.mp3"

        result = subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "mp3",
             "-o", str(audio_file), url],
            capture_output=True, text=True
        )

        if result.returncode != 0 or not audio_file.exists():
            raise DownloadError(f"YouTube download failed: {result.stderr}")

        logger.info("YouTube download complete")
        return audio_file

    def _download_generic(self, url: str, name: str) -> Path:
        """Download from generic URL with format conversion."""
        import time
        logger.info("Using generic download...")

        tmp_dir = self.config.script_dir / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        timestamp = int(time.time() * 1000)

        # Get file extension
        ext = Path(url).suffix.lstrip(".").lower() or "mp3"
        if ext not in ["m4a", "aac", "wav", "flac", "ogg", "mp3"]:
            ext = "mp3"

        audio_file = tmp_dir / f"generic_audio_{name}_{timestamp}.{ext}"
        mp3_file = tmp_dir / f"generic_audio_{name}_{timestamp}.mp3"

        result = subprocess.run(
            ["curl", "-L", "-o", str(audio_file), url],
            capture_output=True, text=True
        )

        if result.returncode != 0 or not audio_file.exists():
            raise DownloadError(f"Generic download failed: {result.stderr}")

        # Convert to MP3 if needed
        if ext == "mp3":
            audio_file.rename(mp3_file)
            audio_file = mp3_file
        else:
            audio_file = self._extract_audio(audio_file, mp3_file)

        logger.info("Generic download complete")
        return audio_file

    def _extract_audio(self, video_path: Path, output_path: Path) -> Path:
        """Extract audio from video file using ffmpeg to specified output path."""
        # Try MP3 first
        result = subprocess.run(
            ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "libmp3lame", "-q:a", "2",
             str(output_path), "-y"],
            capture_output=True, text=True
        )

        if result.returncode != 0 or not output_path.exists():
            # Fallback to m4a
            output_path = output_path.with_suffix(".m4a")
            result = subprocess.run(
                ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "copy",
                 str(output_path), "-y"],
                capture_output=True, text=True
            )

        if result.returncode != 0 or not output_path.exists():
            raise DownloadError(f"Audio extraction failed: {result.stderr}")

        return output_path
