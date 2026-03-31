"""LLM client implementations - uses unified provider registry."""

import logging
import requests

from .llm_client import LLMClient, LLMResponse
from .providers import (
    ProviderConfig,
    Capability,
    ApiStyle,
    get_provider_by_capability,
)

logger = logging.getLogger(__name__)


class MiniMaxClient(LLMClient):
    """MiniMax Token Plan client using Anthropic API compatible endpoint.

    Requires ANTHROPIC_API_KEY (Token Plan专属) and model MiniMax-M2.7.
    Docs: https://platform.minimax.io/docs/api-reference/text-anthropic-api
    """

    def __init__(self, api_key: str, model: str = "MiniMax-M2.7", base_url: str | None = None):
        import anthropic
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(
            base_url=base_url or "https://api.minimax.io/anthropic",
            api_key=api_key,
        )

    def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Call MiniMax Token Plan API via Anthropic SDK."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message}
                    ]
                }
            ]
        )

        # Extract text content from response
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        logger.info(f"MiniMax {self.model} response: {len(content)} chars")
        return LLMResponse(content=content)

    @property
    def name(self) -> str:
        return f"MiniMax/{self.model}"


class SiliconFlowLLMClient(LLMClient):
    """SiliconFlow (siliconflow.cn) LLM client.

    Supports DeepSeek-V3.2, Qwen, and other models hosted on SiliconFlow.
    API docs: https://docs.siliconflow.cn/
    """

    def __init__(self, api_key: str, model: str = "deepseek-ai/DeepSeek-V3.2", base_url: str | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.siliconflow.cn/v1"

    def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Call SiliconFlow API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 8000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        logger.info(f"SiliconFlow {self.model} response: {len(content)} chars")
        return LLMResponse(content=content)

    @property
    def name(self) -> str:
        return f"SiliconFlow/{self.model}"


class DeepSeekClient(LLMClient):
    """DeepSeek official API client."""

    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.deepseek.com/v1"

    def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Call DeepSeek official API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 8000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        logger.info(f"DeepSeek {self.model} response: {len(content)} chars")
        return LLMResponse(content=content)

    @property
    def name(self) -> str:
        return f"DeepSeek/{self.model}"


class OpenAIClient(LLMClient):
    """OpenAI API compatible client (also works for Azure OpenAI)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"

    def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Call OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 8000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        logger.info(f"OpenAI {self.model} response: {len(content)} chars")
        return LLMResponse(content=content)

    @property
    def name(self) -> str:
        return f"OpenAI/{self.model}"


class QwenClient(LLMClient):
    """Alibaba Cloud Qwen (百炼/DashScope) API client."""

    def __init__(self, api_key: str, model: str = "qwen-plus", base_url: str | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Call Alibaba Cloud Qwen API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 8000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        logger.info(f"Qwen {self.model} response: {len(content)} chars")
        return LLMResponse(content=content)

    @property
    def name(self) -> str:
        return f"Qwen/{self.model}"


class OpenRouterClient(LLMClient):
    """OpenRouter unified LLM API client.

    OpenRouter provides a unified API to hundreds of models from multiple providers.
    API docs: https://openrouter.ai/docs/api/reference/overview
    """

    def __init__(self, api_key: str, model: str = "google/gemini-2.5-flash", base_url: str | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://openrouter.ai/api/v1"

    def chat(self, system_prompt: str, user_message: str) -> LLMResponse:
        """Call OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 8000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        logger.info(f"OpenRouter {self.model} response: {len(content)} chars")
        return LLMResponse(content=content)

    @property
    def name(self) -> str:
        return f"OpenRouter/{self.model}"


def create_llm_client(
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> LLMClient:
    """Create LLM client based on provider configuration.

    Args:
        provider: Provider name. If None, uses LLM_PROVIDER env var (default: minimax)
        api_key: API key. If None, reads from provider's env var
        model: Model name. If None, uses provider default
        base_url: API base URL. If None, uses provider default

    Returns:
        LLMClient instance
    """
    config = get_provider_by_capability(Capability.LLM, provider)

    # Get API key from env if not provided
    if api_key is None:
        api_key = config.get_api_key()
    if not api_key:
        raise ValueError(f"API key not found for provider: {config.name}")

    # Use default model if not specified
    if model is None:
        model = config.llm_model
    if not model:
        raise ValueError(f"No default model for provider: {config.name}")

    # Use base_url from config if not specified
    if base_url is None:
        base_url = config.base_url

    # Create client based on API style
    if config.api_style == ApiStyle.ANTHROPIC:
        return MiniMaxClient(api_key=api_key, model=model, base_url=base_url)
    else:
        # REST-style clients
        client_map = {
            "siliconflow": SiliconFlowLLMClient,
            "deepseek": DeepSeekClient,
            "openai": OpenAIClient,
            "qwen": QwenClient,
            "openrouter": OpenRouterClient,
        }
        client_class = client_map.get(config.name.lower())
        if client_class:
            return client_class(api_key=api_key, model=model, base_url=base_url)
        raise ValueError(f"No LLM client for provider: {config.name}")
