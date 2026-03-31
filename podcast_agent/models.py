"""Data models for podcast transcription workflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to Whisper timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


@dataclass
class TranscriptSegment:
    """A single segment of transcript with timestamp."""
    start: str
    end: str
    text: str


@dataclass
class Transcript:
    """Full transcript from transcription provider."""
    segments: list[TranscriptSegment]
    source_path: Path

    @classmethod
    def from_whisper_json(cls, path: Path) -> "Transcript":
        """Parse transcript from Whisper.cpp JSON output file."""
        import json

        data = json.loads(path.read_text(encoding="utf-8"))

        segments = []
        for seg in data.get("transcription", []):
            ts = seg.get("timestamps", {})
            segments.append(TranscriptSegment(
                start=ts.get("from", "00:00:00,000"),
                end=ts.get("to", "00:00:00,000"),
                text=seg.get("text", "").strip()
            ))

        return cls(segments=segments, source_path=path)

    @classmethod
    def from_openai_response(cls, data: dict, source_path: Path) -> "Transcript":
        """Parse transcript from OpenAI Whisper API response.

        OpenAI response format:
        {
            "text": "...",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 4.0,
                    "text": "..."
                }
            ]
        }
        """
        segments = []
        for seg in data.get("segments", []):
            segments.append(TranscriptSegment(
                start=_seconds_to_timestamp(seg.get("start", 0.0)),
                end=_seconds_to_timestamp(seg.get("end", 0.0)),
                text=seg.get("text", "").strip()
            ))

        return cls(segments=segments, source_path=source_path)

    @classmethod
    def from_siliconflow_response(cls, data: dict, source_path: Path) -> "Transcript":
        """Parse transcript from SiliconFlow Whisper API response.

        SiliconFlow returns simple format: { "text": "..." }
        No segments with timestamps, just full text.
        """
        segments = []
        text = data.get("text", "").strip()
        if text:
            # SiliconFlow doesn't provide timestamps, use 0:00 as placeholder
            segments.append(TranscriptSegment(
                start="0:00",
                end="0:00",
                text=text
            ))

        return cls(segments=segments, source_path=source_path)

    def get_full_text(self) -> str:
        """Get all text content without timestamps."""
        return "\n".join(seg.text for seg in self.segments)


@dataclass
class TextSource:
    """Text content from any source (transcript or subtitle)."""
    source_type: str  # "whisper", "subtitle_zh", "subtitle_en_translated"
    full_text: str
    source_path: Path | None = None

    def get_full_text(self) -> str:
        """Get all text content."""
        return self.full_text


@dataclass
class Summary:
    """AI-generated summary result."""
    content: str
    topic: str = ""


@dataclass
class ProcessingResult:
    """Result of the complete processing pipeline."""
    audio_path: Path
    transcript: Transcript
    document_path: Path
    brief: Summary
