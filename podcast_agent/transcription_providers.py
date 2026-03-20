"""Transcription provider implementations - uses unified provider registry."""

import asyncio
import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import requests

from .config import Config
from .models import Transcript
from .providers import (
    ProviderConfig,
    Capability,
    ApiStyle,
    ProviderType,
    get_provider_by_capability,
)

logger = logging.getLogger(__name__)


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""

    @abstractmethod
    async def transcribe_async(self, audio_path: Path) -> Transcript:
        """Transcribe audio file asynchronously."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass


class WhisperCppProvider(TranscriptionProvider):
    """Local Whisper.cpp provider."""

    def __init__(self, config: ProviderConfig, timeout: int = 600, max_retries: int = 3):
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries

    async def transcribe_async(self, audio_path: Path) -> Transcript:
        """Transcribe using local Whisper.cpp CLI."""
        logger.info("[WhisperCpp] Starting transcription...")

        for attempt in range(self.max_retries):
            try:
                transcript = await self._transcribe_once(audio_path)
                logger.info("[WhisperCpp] Transcription complete")
                return transcript
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"[WhisperCpp] Failed: {e}, retrying ({attempt + 1}/{self.max_retries})")
                    continue
                raise

        raise RuntimeError(f"WhisperCpp transcription failed after {self.max_retries} attempts")

    async def _transcribe_once(self, audio_path: Path) -> Transcript:
        """Single transcription attempt with timeout."""
        timestamp = asyncio.get_event_loop().time()
        output_path = Path(tempfile.gettempdir()) / f"whisper_{timestamp}"

        cli_path = self.config.get_cli_path()
        model_path = self.config.get_model_path()

        if not cli_path or not cli_path.exists():
            raise FileNotFoundError(f"Whisper CLI not found: {cli_path}")
        if not model_path or not model_path.exists():
            raise FileNotFoundError(f"Whisper model not found: {model_path}")

        cmd = [
            str(cli_path),
            "-m", str(model_path),
            "-f", str(audio_path),
            "--language", "zh",
            "-oj", "-of", str(output_path), "-np"
        ]

        logger.info(f"[WhisperCpp] Running: {' '.join(cmd)}")

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
            raise RuntimeError(f"WhisperCpp timed out after {self.timeout}s")

        if proc.returncode != 0:
            raise RuntimeError(f"WhisperCpp failed: {stderr.decode()}")

        # Check for output file (JSON)
        json_path = Path(f"{output_path}.json")
        if not json_path.exists():
            raise RuntimeError("WhisperCpp output file not found")

        return Transcript.from_whisper_json(json_path)

    @property
    def name(self) -> str:
        return "WhisperCpp"


class OpenAIWhisperProvider(TranscriptionProvider):
    """OpenAI Whisper API provider."""

    def __init__(self, config: ProviderConfig, model: str = "whisper-1", timeout: int = 300):
        self.config = config
        self.model = model
        self.timeout = timeout
        self.base_url = config.base_url or "https://api.openai.com/v1"

    async def transcribe_async(self, audio_path: Path) -> Transcript:
        """Transcribe using OpenAI Whisper API."""
        logger.info(f"[OpenAI Whisper] Starting transcription with model {self.model}...")

        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(None, self._transcribe_sync, audio_path)

        logger.info("[OpenAI Whisper] Transcription complete")
        return transcript

    def _transcribe_sync(self, audio_path: Path) -> Transcript:
        """Synchronous transcription via OpenAI API."""
        api_key = self.config.get_api_key()
        if not api_key:
            raise ValueError(f"API key not found for {self.config.name}")

        with open(audio_path, "rb") as audio_file:
            files = {"file": audio_file}
            data = {"model": self.model, "language": "zh", "response_format": "verbose_json"}
            headers = {"Authorization": f"Bearer {api_key}"}

            response = requests.post(
                f"{self.base_url}/audio/transcriptions",
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout
            )

        response.raise_for_status()
        result = response.json()

        return Transcript.from_openai_response(result, audio_path)

    @property
    def name(self) -> str:
        return f"OpenAI/{self.model}"


class SiliconFlowWhisperProvider(TranscriptionProvider):
    """SiliconFlow Whisper API provider."""

    def __init__(self, config: ProviderConfig, model: str = "FunAudioLLM/SenseVoiceLarge", timeout: int = 300):
        self.config = config
        self.model = model
        self.timeout = timeout
        self.base_url = config.base_url or "https://api.siliconflow.cn/v1"

    async def transcribe_async(self, audio_path: Path) -> Transcript:
        """Transcribe using SiliconFlow Whisper API."""
        logger.info(f"[SiliconFlow Whisper] Starting transcription with model {self.model}...")

        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(None, self._transcribe_sync, audio_path)

        logger.info("[SiliconFlow Whisper] Transcription complete")
        return transcript

    def _transcribe_sync(self, audio_path: Path) -> Transcript:
        """Synchronous transcription via SiliconFlow API."""
        api_key = self.config.get_api_key()
        if not api_key:
            raise ValueError(f"API key not found for {self.config.name}")

        with open(audio_path, "rb") as audio_file:
            files = {"file": audio_file}
            data = {"model": self.model, "language": "zh", "response_format": "verbose_json"}
            headers = {"Authorization": f"Bearer {api_key}"}

            response = requests.post(
                f"{self.base_url}/audio/transcriptions",
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout
            )

        response.raise_for_status()
        result = response.json()

        return Transcript.from_siliconflow_response(result, audio_path)

    @property
    def name(self) -> str:
        return f"SiliconFlow/{self.model}"


def create_transcription_provider(
    config: Config | None = None,
    provider: str | None = None,
    model: str | None = None,
    timeout: int = 600,
    max_retries: int = 3,
) -> TranscriptionProvider:
    """Create transcription provider based on configuration.

    Args:
        config: Application Config (used for timeout/retry settings)
        provider: Provider name. If None, uses TRANSCRIPTION_PROVIDER env var
        model: Model name. If None, uses provider default
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        TranscriptionProvider instance
    """
    provider_config = get_provider_by_capability(Capability.TRANSCRIPTION, provider)

    if provider_config.provider_type == ProviderType.LOCAL:
        return WhisperCppProvider(provider_config, timeout=timeout, max_retries=max_retries)
    else:
        # Remote API providers
        transcription_model = model or provider_config.transcription_model

        if provider_config.name.lower() == "openai":
            return OpenAIWhisperProvider(provider_config, model=transcription_model, timeout=timeout)
        elif provider_config.name.lower() == "siliconflow":
            return SiliconFlowWhisperProvider(provider_config, model=transcription_model, timeout=timeout)
        else:
            raise ValueError(f"Unknown transcription provider: {provider_config.name}")
