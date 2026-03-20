"""Transcriber module - handles Whisper.cpp transcription with timeout and retry."""

import asyncio
import logging
import tempfile
from pathlib import Path
import os

from .config import Config
from .models import Transcript

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass


class TranscriptionTimeoutError(TranscriptionError):
    """Raised when transcription times out."""
    pass


class Transcriber:
    """Transcribes audio files using Whisper.cpp."""

    def __init__(self, config: Config):
        self.config = config
        self.timeout = config.default_timeout
        self.max_retries = config.max_retries

    async def transcribe_async(self, audio_path: Path) -> Transcript:
        """Transcribe audio file asynchronously with timeout and retry.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcript object with segments
        """
        logger.info("Starting transcription...")

        for attempt in range(self.max_retries):
            try:
                transcript = await self._transcribe_once(audio_path)
                logger.info("Transcription complete")
                return transcript
            except TranscriptionTimeoutError:
                logger.warning(f"Transcription timeout, retrying ({attempt + 1}/{self.max_retries})")
                continue
            except TranscriptionError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Transcription failed: {e}, retrying ({attempt + 1}/{self.max_retries})")
                    continue
                raise

        raise TranscriptionError(f"Transcription failed after {self.max_retries} attempts")

    async def _transcribe_once(self, audio_path: Path) -> Transcript:
        """Single transcription attempt with timeout."""
        timestamp = asyncio.get_event_loop().time()
        output_path = Path(tempfile.gettempdir()) / f"whisper_{timestamp}"

        cmd = [
            str(self.config.whisper_cli),
            "-m", str(self.config.whisper_model),
            "-f", str(audio_path),
            "--language", "zh",
            "-oj", "-of", str(output_path), "-np"
        ]

        logger.info(f"Running whisper: {' '.join(cmd)}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise TranscriptionTimeoutError(f"Whisper timed out after {self.timeout}s")

        if proc.returncode != 0:
            raise TranscriptionError(f"Whisper failed: {stderr.decode()}")

        # Check for output file (JSON)
        json_path = Path(f"{output_path}.json")
        if not json_path.exists():
            raise TranscriptionError("Transcription output file not found")

        # Copy to transcription directory
        dest_name = f"trans_{timestamp}.json"
        dest_path = self.config.transcription_dir / dest_name
        json_path.rename(dest_path)

        return Transcript.from_file(dest_path)

    def transcribe(self, audio_path: Path) -> Transcript:
        """Synchronous wrapper for transcribe_async."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.transcribe_async(audio_path))
