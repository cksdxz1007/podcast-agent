"""Data models for podcast transcription workflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TranscriptSegment:
    """A single segment of transcript with timestamp."""
    start: str
    end: str
    text: str


@dataclass
class Transcript:
    """Full transcript from Whisper output."""
    segments: list[TranscriptSegment]
    source_path: Path

    @classmethod
    def from_file(cls, path: Path) -> "Transcript":
        """Parse transcript from Whisper JSON output file."""
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

    def get_full_text(self) -> str:
        """Get all text content without timestamps."""
        return "\n".join(seg.text for seg in self.segments)


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
