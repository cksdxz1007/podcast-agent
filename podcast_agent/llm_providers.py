"""LLM client implementations for various providers."""

import os
import logging
import requests

from .llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


class MiniMaxClient(LLMClient):
    """MiniMax Token Plan client using Anthropic API compatible endpoint.

    Requires ANTHROPIC_API_KEY (Token Plan专属) and model MiniMax-M2.7.
    Docs: https://platform.minimax.io/docs/api-reference/text-anthropic-api
    """

    def __init__(self, api_key: str, model: str = "MiniMax-M2.7"):
        import anthropic
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(
            base_url="https://api.minimax.io/anthropic",
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


class SiliconFlowClient(LLMClient):
    """SiliconFlow (siliconflow.cn) LLM client.

    Supports DeepSeek-V3.2, Qwen, and other models hosted on SiliconFlow.
    API docs: https://docs.siliconflow.cn/
    """

    BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "deepseek-ai/DeepSeek-V3.2"):
        self.api_key = api_key
        self.model = model

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
            self.BASE_URL,
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


class DeepSeekOfficialClient(LLMClient):
    """DeepSeek official API client."""

    BASE_URL = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model

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
            self.BASE_URL,
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

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or self.BASE_URL

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

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "qwen-plus"):
        self.api_key = api_key
        self.model = model

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
            self.BASE_URL,
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


def create_llm_client(provider: str = None, api_key: str = None, model: str = None) -> LLMClient:
    """Factory function to create LLM client based on provider.

    Args:
        provider: Provider name ("siliconflow", "deepseek", "openai", "qwen", "minimax")
                  If None, reads from LLM_PROVIDER env var
        api_key: API key. If None, reads from corresponding env var:
                 - SILICONFLOW_API_KEY
                 - DEEPSEEK_API_KEY
                 - OPENAI_API_KEY
                 - DASHSCOPE_API_KEY
                 - ANTHROPIC_API_KEY (for minimax)
        model: Model name. If None, uses provider default

    Returns:
        LLMClient instance
    """
    if provider is None:
        provider = os.environ.get("LLM_PROVIDER", "minimax").lower()

    if api_key is None:
        env_vars = {
            "siliconflow": "SILICONFLOW_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
            "qwen": "DASHSCOPE_API_KEY",
            "minimax": "ANTHROPIC_API_KEY",
        }
        api_key = os.environ.get(env_vars.get(provider, ""))

    if not api_key:
        raise ValueError(f"API key not found for provider: {provider}")

    if model is None:
        defaults = {
            "siliconflow": "deepseek-ai/DeepSeek-V3.2",
            "deepseek": "deepseek-chat",
            "openai": "gpt-4o",
            "qwen": "qwen-plus",
            "minimax": "MiniMax-M2.7",
        }
        model = defaults.get(provider, "gpt-4o")

    clients = {
        "siliconflow": SiliconFlowClient,
        "deepseek": DeepSeekOfficialClient,
        "openai": OpenAIClient,
        "qwen": QwenClient,
        "minimax": MiniMaxClient,
    }

    client_class = clients.get(provider)
    if client_class is None:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(clients.keys())}")

    return client_class(api_key=api_key, model=model)
