import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(frozen=True)
class OpenAIResponsesConfig:
    api_key: str
    model: str
    timeout_seconds: float


class OpenAIResponsesClient:
    def __init__(self, config: OpenAIResponsesConfig | None = None) -> None:
        self.config = config or load_openai_config()

    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    def create_json_response(self, *, input_messages: list[dict[str, str]], json_schema: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        payload = {
            "model": self.config.model,
            "input": [
                {
                    "role": item["role"],
                    "content": [{"type": "input_text", "text": item["content"]}],
                }
                for item in input_messages
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "restaurant_agent_turn",
                    "strict": True,
                    "schema": json_schema,
                }
            },
            "store": False,
        }
        request = urllib.request.Request(
            OPENAI_RESPONSES_URL,
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
            raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI API connection error: {exc.reason}") from exc

        text = extract_response_text(body)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI response was not valid JSON") from exc


def load_openai_config() -> OpenAIResponsesConfig:
    return OpenAIResponsesConfig(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "chat-latest"),
        timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20")),
    )


def extract_response_text(body: dict[str, Any]) -> str:
    output_text = body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    chunks: list[str] = []
    for item in body.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    text = "\n".join(chunks).strip()
    if not text:
        raise RuntimeError("OpenAI response did not include output text")
    return text
