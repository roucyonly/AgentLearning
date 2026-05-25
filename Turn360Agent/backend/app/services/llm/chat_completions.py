import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChatCompletionsConfig:
    api_key: str
    base_url: str
    model: str
    provider_name: str
    timeout_seconds: float
    max_tokens: int
    extra_body: dict[str, Any] = field(default_factory=dict)


class OpenAICompatibleChatClient:
    def __init__(self, config: ChatCompletionsConfig) -> None:
        self.config = config

    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key and self.config.base_url and self.config.model)

    @property
    def provider_name(self) -> str:
        return self.config.provider_name

    def create_json_response(self, *, input_messages: list[dict[str, str]], json_schema: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError(f"{self.config.provider_name} API key is not configured")

        messages = prepare_json_messages(input_messages, json_schema)
        payload = {
            "model": self.config.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "max_tokens": self.config.max_tokens,
            **self.config.extra_body,
        }
        request = urllib.request.Request(
            f"{self.config.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{self.config.provider_name} API error {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"{self.config.provider_name} API connection error: {exc.reason}") from exc

        text = extract_chat_completion_text(body)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{self.config.provider_name} response was not valid JSON") from exc


def prepare_json_messages(input_messages: list[dict[str, str]], json_schema: dict[str, Any]) -> list[dict[str, str]]:
    messages = [{"role": item["role"], "content": item["content"]} for item in input_messages]
    schema_instruction = (
        "\n\nReturn only valid json. Do not wrap it in markdown. "
        "The json object must match this schema and example shape.\n"
        f"Schema: {json.dumps(json_schema, ensure_ascii=False)}\n"
        "Example json: {"
        '"intent":"pre_opening",'
        '"slot_updates":[{"id":"monthly_rent","value":12000,"confidence":"high"}],'
        '"assistant_reply":"我先把你说清楚的数字放进表里。",'
        '"next_question":"你在门口数30分钟，目标客群有多少人？",'
        '"needs_more_data":true'
        "}"
    )
    if messages and messages[0]["role"] == "system":
        messages[0]["content"] += schema_instruction
    else:
        messages.insert(0, {"role": "system", "content": schema_instruction})
    return messages


def extract_chat_completion_text(body: dict[str, Any]) -> str:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("chat completion response did not include choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("chat completion response did not include message content")
    return content.strip()


def load_deepseek_config() -> ChatCompletionsConfig:
    return ChatCompletionsConfig(
        api_key=os.getenv("DEEPSEEK_API_KEY", os.getenv("LLM_API_KEY", "")),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("DEEPSEEK_MODEL", os.getenv("LLM_MODEL", "deepseek-v4-flash")),
        provider_name="deepseek",
        timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "20"))),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", os.getenv("DEEPSEEK_MAX_TOKENS", "1200"))),
        extra_body={"thinking": {"type": os.getenv("DEEPSEEK_THINKING", "disabled")}},
    )


def load_openai_compatible_config() -> ChatCompletionsConfig:
    return ChatCompletionsConfig(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", ""),
        model=os.getenv("LLM_MODEL", ""),
        provider_name=os.getenv("LLM_PROVIDER_NAME", "openai_compatible"),
        timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "20")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1200")),
    )
