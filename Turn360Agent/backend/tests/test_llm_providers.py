import json
import os
import unittest
from unittest.mock import patch

from app.services.llm.chat_completions import (
    OpenAICompatibleChatClient,
    extract_chat_completion_text,
    load_deepseek_config,
    load_openai_compatible_config,
    prepare_json_messages,
)
from app.services.llm.provider_factory import DisabledLLMClient, load_llm_client


class LLMProviderTest(unittest.TestCase):
    def test_deepseek_config_defaults_to_current_v4_flash(self) -> None:
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "key"}, clear=True):
            config = load_deepseek_config()

        self.assertEqual(config.provider_name, "deepseek")
        self.assertEqual(config.base_url, "https://api.deepseek.com")
        self.assertEqual(config.model, "deepseek-v4-flash")
        self.assertEqual(config.extra_body["thinking"]["type"], "disabled")

    def test_provider_factory_loads_deepseek_client(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "key"}, clear=True):
            client = load_llm_client()

        self.assertIsInstance(client, OpenAICompatibleChatClient)
        self.assertTrue(client.is_configured)
        self.assertEqual(client.provider_name, "deepseek")

    def test_provider_factory_can_disable_llm(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "none"}, clear=True):
            client = load_llm_client()

        self.assertIsInstance(client, DisabledLLMClient)
        self.assertFalse(client.is_configured)

    def test_openai_compatible_requires_base_model_and_key(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai_compatible", "LLM_API_KEY": "key"}, clear=True):
            config = load_openai_compatible_config()
            client = OpenAICompatibleChatClient(config)

        self.assertFalse(client.is_configured)

    def test_prepare_json_messages_includes_json_instruction(self) -> None:
        messages = prepare_json_messages(
            [{"role": "system", "content": "system"}, {"role": "user", "content": "user"}],
            {"type": "object", "properties": {}},
        )

        self.assertIn("valid json", messages[0]["content"])
        self.assertIn("Example json", messages[0]["content"])

    def test_extract_chat_completion_text(self) -> None:
        body = {"choices": [{"message": {"content": json.dumps({"ok": True})}}]}

        self.assertEqual(extract_chat_completion_text(body), '{"ok": true}')


if __name__ == "__main__":
    unittest.main()
