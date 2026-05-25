import os

from app.services.llm.chat_completions import (
    OpenAICompatibleChatClient,
    load_deepseek_config,
    load_openai_compatible_config,
)
from app.services.llm.openai_responses import OpenAIResponsesClient


def load_llm_client():
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider == "deepseek":
        return OpenAICompatibleChatClient(load_deepseek_config())
    if provider in {"openai_compatible", "compatible"}:
        return OpenAICompatibleChatClient(load_openai_compatible_config())
    if provider == "openai":
        return OpenAIResponsesClient()
    if provider in {"none", "disabled", "off"}:
        return DisabledLLMClient(provider)
    raise ValueError(f"unsupported LLM_PROVIDER: {provider}")


class DisabledLLMClient:
    def __init__(self, provider_name: str = "disabled") -> None:
        self.provider_name = provider_name

    @property
    def is_configured(self) -> bool:
        return False

    def create_json_response(self, **_: object) -> dict:
        raise RuntimeError("LLM is disabled")
