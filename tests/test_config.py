from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError

from app.core.config import load_config

OVERRIDE_ENV_NAMES = (
    "ANGLE_FOUNDRY_API_KEY",
    "ANGLE_FOUNDRY_AI_MODEL",
    "ANGLE_FOUNDRY_AI_BASE_URL",
    "ANGLE_FOUNDRY_AI_TIMEOUT_SECONDS",
    "ANGLE_FOUNDRY_AI_MAX_RETRIES",
    "FEISHU_WEBHOOK",
)


def write_config(
    path: Path,
    *,
    topics: str = '["理财"]',
    directions: str | None = None,
    provider: str = '"feishu"',
    webhook: str = '"https://example.com/webhook"',
    model: str = '"test-model"',
    base_url: str = '"https://example.com/api"',
    timeout_seconds: int = 60,
    max_retries: int = 2,
    api_key: str = '"config-api-key"',
) -> None:
    if directions is None:
        directions = '["坑", "盲区", "痛点", "疑问", "跨界话题"]'

    path.write_text(
        f"""
[schedule]
enabled = true
cron = "30 8 * * *"

[generator]
topics = {topics}
directions = {directions}
count_per_direction = 2

[push]
provider = {provider}
webhook = {webhook}

[ai]
model = {model}
base_url = {base_url}
timeout_seconds = {timeout_seconds}
max_retries = {max_retries}
api_key = {api_key}
""".strip(),
        encoding="utf-8",
    )


class LoadConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.tmp_dir.name) / "config.toml"
        self.original_env = {
            name: os.environ.get(name)
            for name in OVERRIDE_ENV_NAMES
        }

    def tearDown(self) -> None:
        for name, value in self.original_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.tmp_dir.cleanup()

    def clear_override_envs(self) -> None:
        for name in OVERRIDE_ENV_NAMES:
            os.environ.pop(name, None)

    def test_load_config_reads_toml_and_env(self) -> None:
        write_config(self.config_path)
        self.clear_override_envs()
        os.environ["ANGLE_FOUNDRY_API_KEY"] = "secret-key"

        config = load_config(self.config_path)

        self.assertEqual(config.topics, ["理财"])
        self.assertEqual(config.directions, ["坑", "盲区", "痛点", "疑问", "跨界话题"])
        self.assertEqual(config.push_provider, "feishu")
        self.assertEqual(config.ai_api_key, "secret-key")

    def test_load_config_falls_back_to_toml_when_env_missing(self) -> None:
        write_config(self.config_path)
        self.clear_override_envs()

        config = load_config(self.config_path)

        self.assertEqual(config.ai_api_key, "config-api-key")
        self.assertEqual(config.ai_model, "test-model")
        self.assertEqual(config.ai_base_url, "https://example.com/api")
        self.assertEqual(config.ai_timeout_seconds, 60)
        self.assertEqual(config.ai_max_retries, 2)
        self.assertEqual(config.push_webhook, "https://example.com/webhook")

    def test_load_config_env_override_takes_precedence(self) -> None:
        write_config(
            self.config_path,
            webhook='"https://example.com/config-webhook"',
            model='"config-model"',
            base_url='"https://example.com/config-api"',
            timeout_seconds=60,
            max_retries=2,
            api_key='"config-api-key"',
        )
        self.clear_override_envs()
        os.environ["ANGLE_FOUNDRY_API_KEY"] = "env-api-key"
        os.environ["ANGLE_FOUNDRY_AI_MODEL"] = "env-model"
        os.environ["ANGLE_FOUNDRY_AI_BASE_URL"] = "https://example.com/env-api"
        os.environ["ANGLE_FOUNDRY_AI_TIMEOUT_SECONDS"] = "15"
        os.environ["ANGLE_FOUNDRY_AI_MAX_RETRIES"] = "4"
        os.environ["FEISHU_WEBHOOK"] = "https://example.com/env-webhook"

        config = load_config(self.config_path)

        self.assertEqual(config.ai_api_key, "env-api-key")
        self.assertEqual(config.ai_model, "env-model")
        self.assertEqual(config.ai_base_url, "https://example.com/env-api")
        self.assertEqual(config.ai_timeout_seconds, 15)
        self.assertEqual(config.ai_max_retries, 4)
        self.assertEqual(config.push_webhook, "https://example.com/env-webhook")

    def test_load_config_uses_all_env_overrides_when_present(self) -> None:
        write_config(
            self.config_path,
            webhook='"https://example.com/config-webhook"',
            model='"config-model"',
            base_url='"https://example.com/config-api"',
            timeout_seconds=60,
            max_retries=2,
            api_key='"config-api-key"',
        )
        self.clear_override_envs()
        env_values = {
            "ANGLE_FOUNDRY_API_KEY": "env-api-key",
            "ANGLE_FOUNDRY_AI_BASE_URL": "https://example.com/env-api",
            "ANGLE_FOUNDRY_AI_MODEL": "env-model",
            "ANGLE_FOUNDRY_AI_TIMEOUT_SECONDS": "15",
            "ANGLE_FOUNDRY_AI_MAX_RETRIES": "4",
            "FEISHU_WEBHOOK": "https://example.com/env-webhook",
        }
        os.environ.update(env_values)

        config = load_config(self.config_path)

        self.assertEqual(config.ai_api_key, env_values["ANGLE_FOUNDRY_API_KEY"])
        self.assertEqual(
            config.ai_base_url, env_values["ANGLE_FOUNDRY_AI_BASE_URL"]
        )
        self.assertEqual(config.ai_model, env_values["ANGLE_FOUNDRY_AI_MODEL"])
        self.assertEqual(config.ai_timeout_seconds, 15)
        self.assertEqual(config.ai_max_retries, 4)
        self.assertEqual(config.push_webhook, env_values["FEISHU_WEBHOOK"])

    def test_load_config_validates_constraints(self) -> None:
        cases = [
            ('[]', None, '"feishu"', 60, 2, "topics must be a non-empty list"),
            ('["理财"]', '["坑", "盲区"]', '"feishu"', 60, 2, "directions must be exactly"),
            ('["理财"]', None, '"slack"', 60, 2, "Input should be 'feishu' or 'wecom'"),
            ('["理财"]', None, '"feishu"', 0, 2, "greater than 0"),
            ('["理财"]', None, '"feishu"', 60, -1, "greater than or equal to 0"),
        ]
        self.clear_override_envs()
        os.environ["ANGLE_FOUNDRY_API_KEY"] = "secret-key"

        for topics, directions, provider, timeout_seconds, max_retries, message in cases:
            with self.subTest(message=message):
                write_config(
                    self.config_path,
                    topics=topics,
                    directions=directions,
                    provider=provider,
                    timeout_seconds=timeout_seconds,
                    max_retries=max_retries,
                )

                with self.assertRaisesRegex(ValidationError, message):
                    load_config(self.config_path)
