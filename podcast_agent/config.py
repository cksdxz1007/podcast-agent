"""Configuration module - loads settings from environment and config files."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

logger = __import__("logging").getLogger(__name__)


@dataclass
class Config:
    """Application configuration loaded from environment and config files."""

    # Paths
    script_dir: Path
    whisper_model: Path
    whisper_cli: Path
    cookie_file: Path
    youtube_cookie_file: Path
    transcription_dir: Path
    document_dir: Path
    openclaw_bin: Path

    # API settings
    deepseek_api_key: str
    telegram_user_id: str
    feishu_user_id: str

    # Transcription provider settings
    transcription_provider: str = "whispercpp"
    openai_whisper_model: str = "whisper-1"
    siliconflow_whisper_model: str = "FunAudioLLM/SenseVoiceLarge"

    # OpenAI/SiliconFlow API keys (for transcription)
    openai_api_key: str = ""
    siliconflow_api_key: str = ""

    # Defaults
    default_timeout: int = 600
    max_retries: int = 3

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment and config files."""
        # Load .env from multiple locations
        env_files = [
            Path.home() / ".openclaw" / ".env",
            Path.home() / ".api_keys",
        ]
        for env_path in env_files:
            if env_path.exists():
                load_dotenv(env_path)

        script_dir = Path(__file__).parent.parent.resolve()

        return cls(
            script_dir=script_dir,
            whisper_model=Path(os.environ.get(
                "WHISPER_MODEL",
                str(Path.home() / "Desktop" / "whisper.cpp" / "models" / "ggml-medium.bin")
            )),
            whisper_cli=Path(os.environ.get(
                "WHISPER_CLI",
                str(Path.home() / "Desktop" / "whisper.cpp" / "build" / "bin" / "whisper-cli")
            )),
            cookie_file=Path(os.environ.get(
                "BILIBILI_COOKIE_FILE",
                str(script_dir / "bilibili_cookies.txt")
            )),
            youtube_cookie_file=Path(os.environ.get(
                "YOUTUBE_COOKIE_FILE",
                str(script_dir / "youtube_cookies.txt")
            )),
            transcription_dir=script_dir / "transcriptions",
            document_dir=script_dir / "documents",
            openclaw_bin=Path(os.environ.get(
                "OPENCLAW_BIN",
                str(Path.home() / ".nvm" / "versions" / "node" / "v22.22.1" / "bin" / "openclaw")
            )),
            deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            telegram_user_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            feishu_user_id=os.environ.get("FEISHU_USER_ID", ""),
            transcription_provider=os.environ.get("TRANSCRIPTION_PROVIDER", "whispercpp"),
            openai_whisper_model=os.environ.get("OPENAI_WHISPER_MODEL", "whisper-1"),
            siliconflow_whisper_model=os.environ.get("SILICONFLOW_WHISPER_MODEL", "FunAudioLLM/SenseVoiceLarge"),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            siliconflow_api_key=os.environ.get("SILICONFLOW_API_KEY", ""),
        )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for dir_path in [self.transcription_dir, self.document_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
