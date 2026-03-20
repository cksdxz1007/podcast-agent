"""Unified provider registry for LLM and transcription services.

Configuration files:
    ~/.api_keys - API keys (loaded via python-dotenv)
    ~/.llm_providers - Provider model configurations

Environment variables (can override config files):
    TRANSCRIPTION_PROVIDER=whispercpp|openai|siliconflow
    LLM_PROVIDER=minimax|siliconflow|deepseek|openai|qwen
    WHISPER_CLI=/path/to/whisper-cli
    WHISPER_MODEL=/path/to/ggml-medium.bin
"""

import os
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class Capability(Enum):
    """Service capabilities that providers can offer."""
    LLM = "llm"
    TRANSCRIPTION = "transcription"


class ProviderType(Enum):
    """Type of provider."""
    LOCAL = "local"   # Local tool (e.g., whisper.cpp)
    REMOTE = "remote"  # Remote API


class ApiStyle(Enum):
    """API call style."""
    REST = "rest"           # Standard REST API (requests)
    ANTHROPIC = "anthropic" # Anthropic SDK


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""
    name: str
    provider_type: ProviderType
    api_key_env: str | None = None  # Environment variable name for API key
    base_url: str | None = None
    auth_type: str = "bearer"
    capabilities: list[Capability] | None = None
    llm_model: str | None = None
    transcription_model: str | None = None
    # Local tool paths (for ProviderType.LOCAL)
    cli_path: Path | None = None       # Direct path (from config file)
    cli_path_env: str | None = None    # Env var name for CLI path
    model_path: Path | None = None      # Direct path (from config file)
    model_path_env: str | None = None   # Env var name for model path
    api_style: ApiStyle = ApiStyle.REST

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = [Capability.LLM]

    def get_api_key(self) -> str | None:
        """Get API key from environment."""
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return None

    def get_cli_path(self) -> Path | None:
        """Get CLI path. Priority: cli_path > env var."""
        if self.cli_path:
            return self.cli_path
        if self.cli_path_env:
            path = os.environ.get(self.cli_path_env)
            if path:
                return Path(path).expanduser()
        return None

    def get_model_path(self) -> Path | None:
        """Get model path. Priority: model_path > env var."""
        if self.model_path:
            return self.model_path
        if self.model_path_env:
            path = os.environ.get(self.model_path_env)
            if path:
                return Path(path).expanduser()
        return None


# Base provider registry (model names will be overridden by ~/.llm_providers)
_PROVIDER_DEFAULTS: dict[str, ProviderConfig] = {
    "minimax": ProviderConfig(
        name="MiniMax",
        provider_type=ProviderType.REMOTE,
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.minimax.io/anthropic",
        capabilities=[Capability.LLM],
        llm_model="MiniMax-M2.7",
        api_style=ApiStyle.ANTHROPIC,
    ),
    "siliconflow": ProviderConfig(
        name="SiliconFlow",
        provider_type=ProviderType.REMOTE,
        api_key_env="SILICONFLOW_API_KEY",
        base_url="https://api.siliconflow.cn/v1",
        capabilities=[Capability.LLM, Capability.TRANSCRIPTION],
        llm_model="deepseek-ai/DeepSeek-V3.2",
        transcription_model="FunAudioLLM/SenseVoiceLarge",
        api_style=ApiStyle.REST,
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        provider_type=ProviderType.REMOTE,
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        capabilities=[Capability.LLM, Capability.TRANSCRIPTION],
        llm_model="gpt-4o",
        transcription_model="whisper-1",
        api_style=ApiStyle.REST,
    ),
    "deepseek": ProviderConfig(
        name="DeepSeek",
        provider_type=ProviderType.REMOTE,
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        capabilities=[Capability.LLM],
        llm_model="deepseek-chat",
        api_style=ApiStyle.REST,
    ),
    "qwen": ProviderConfig(
        name="Qwen",
        provider_type=ProviderType.REMOTE,
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        capabilities=[Capability.LLM],
        llm_model="qwen-plus",
        api_style=ApiStyle.REST,
    ),
    "whispercpp": ProviderConfig(
        name="Whisper.cpp",
        provider_type=ProviderType.LOCAL,
        capabilities=[Capability.TRANSCRIPTION],
        cli_path_env="WHISPER_CLI",
        model_path_env="WHISPER_MODEL",
        api_style=ApiStyle.REST,
    ),
}

# Runtime provider registry (initialized from config files)
PROVIDERS: dict[str, ProviderConfig] = {}


def _load_providers_config() -> None:
    """Load provider configurations from ~/.llm_providers file."""
    config_file = Path.home() / ".llm_providers"

    # Default provider names (can be overridden by config file)
    global _default_llm_provider, _default_transcription_provider
    _default_llm_provider = os.environ.get("LLM_PROVIDER", "minimax").lower()
    _default_transcription_provider = os.environ.get("TRANSCRIPTION_PROVIDER", "whispercpp").lower()

    if config_file.exists():
        from dotenv import dotenv_values
        values = dotenv_values(config_file)

        # First pass: read provider selections
        if "LLM_PROVIDER" in values and values["LLM_PROVIDER"]:
            _default_llm_provider = values["LLM_PROVIDER"].lower()
        if "TRANSCRIPTION_PROVIDER" in values and values["TRANSCRIPTION_PROVIDER"]:
            _default_transcription_provider = values["TRANSCRIPTION_PROVIDER"].lower()

        for provider_name, config in _PROVIDER_DEFAULTS.items():
            # Build override dict
            overrides = {}

            for key, value in values.items():
                key_upper = key.upper()

                # Handle whispercpp paths FIRST (special case - needs Path conversion)
                if provider_name == "whispercpp":
                    if key_upper == "WHISPERCPP_CLI_PATH":
                        overrides["cli_path"] = Path(value).expanduser() if value else None
                    elif key_upper == "WHISPERCPP_MODEL_PATH":
                        overrides["model_path"] = Path(value).expanduser() if value else None
                    continue  # Skip prefix check for whispercpp

                # Provider-specific prefix (e.g., MINIMAX_LLM_MODEL)
                prefix = f"{provider_name.upper()}_"
                if key_upper.startswith(prefix):
                    config_key = key[len(prefix):].lower()
                    overrides[config_key] = value
                    continue

                # Default LLM_MODEL / TRANSCRIPTION_MODEL (no prefix for default provider)
                if key_upper == "LLM_MODEL" and provider_name == _default_llm_provider:
                    overrides["llm_model"] = value
                elif key_upper == "TRANSCRIPTION_MODEL" and provider_name == _default_transcription_provider:
                    overrides["transcription_model"] = value

            # Apply overrides
            if overrides:
                config = ProviderConfig(
                    name=config.name,
                    provider_type=config.provider_type,
                    api_key_env=config.api_key_env,
                    base_url=overrides.get("base_url", config.base_url),
                    auth_type=config.auth_type,
                    capabilities=config.capabilities,
                    llm_model=overrides.get("llm_model", config.llm_model),
                    transcription_model=overrides.get("transcription_model", config.transcription_model),
                    cli_path=overrides.get("cli_path"),
                    cli_path_env=config.cli_path_env,
                    model_path=overrides.get("model_path"),
                    model_path_env=config.model_path_env,
                    api_style=config.api_style,
                )
            PROVIDERS[provider_name] = config
    else:
        # Use defaults
        PROVIDERS.update(_PROVIDER_DEFAULTS)

    logger.info(f"Loaded providers: {list(PROVIDERS.keys())}")
    logger.info(f"Default LLM provider: {_default_llm_provider}")
    logger.info(f"Default transcription provider: {_default_transcription_provider}")


# Module-level defaults (set by _load_providers_config)
_default_llm_provider = "minimax"
_default_transcription_provider = "whispercpp"


def _get_default_llm_provider() -> str:
    return _default_llm_provider


def _get_default_transcription_provider() -> str:
    return _default_transcription_provider


def get_provider_config(name: str) -> ProviderConfig | None:
    """Get provider config by name."""
    if not PROVIDERS:
        _load_providers_config()
    return PROVIDERS.get(name.lower())


def get_llm_provider_name() -> str:
    """Get configured LLM provider name from environment."""
    return _get_default_llm_provider()


def get_transcription_provider_name() -> str:
    """Get configured transcription provider name from environment."""
    return _get_default_transcription_provider()


def get_provider_by_capability(
    capability: Capability,
    provider_name: str | None = None,
) -> ProviderConfig:
    """Get provider config by capability.

    Args:
        capability: The capability to look for
        provider_name: Specific provider name, or None to use default from env

    Returns:
        ProviderConfig for the requested capability

    Raises:
        ValueError: If provider not found or doesn't support the capability
    """
    if not PROVIDERS:
        _load_providers_config()

    if provider_name is None:
        if capability == Capability.LLM:
            provider_name = get_llm_provider_name()
        elif capability == Capability.TRANSCRIPTION:
            provider_name = get_transcription_provider_name()

    config = get_provider_config(provider_name)
    if not config:
        available = list(PROVIDERS.keys())
        raise ValueError(
            f"Unknown provider: {provider_name}. Available: {available}"
        )

    if config.capabilities is None or capability not in config.capabilities:
        caps_str = [c.value for c in config.capabilities] if config.capabilities else []
        raise ValueError(
            f"Provider '{provider_name}' does not support {capability.value}. "
            f"Supported: {caps_str}"
        )

    return config


# Initialize on import
_load_providers_config()
