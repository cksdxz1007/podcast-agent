"""Transcriber module - facade for transcription providers."""

import asyncio
import logging
from pathlib import Path

from .config import Config
from .models import Transcript
from .transcription_providers import (
    TranscriptionProvider,
    create_transcription_provider,
)

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass


class Transcriber:
    """Transcribes audio files using configurable transcription provider."""

    def __init__(self, config: Config):
        self.config = config
        self.provider: TranscriptionProvider = create_transcription_provider(
            config=config,
            timeout=config.default_timeout,
            max_retries=config.max_retries,
        )
        logger.info(f"Using transcription provider: {self.provider.name}")

    async def transcribe_async(self, audio_path: Path) -> Transcript:
        """Transcribe audio file asynchronously.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcript object with segments

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            return await self.provider.transcribe_async(audio_path)
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e

    def transcribe(self, audio_path: Path) -> Transcript:
        """Synchronous wrapper for transcribe_async."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.transcribe_async(audio_path))
