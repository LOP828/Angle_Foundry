from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError

from app.core.config import load_config


def write_config(
    path: Path,
    *,
    topics: str = '["理财"]',
    directions: str | None = None,
    provider: str = '"feishu"',
    timeout_seconds: int = 60,
    max_retries: int = 2,
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
webhook = "https://example.com/webhook"

[ai]
model = "test-model"
base_url = "https://example.com/api"
timeout_seconds = {timeout_seconds}
max_retries = {max_retries}
""".strip(),
        encoding="utf-8",
    )


class LoadConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.tmp_dir.name) / "config.toml"
        self.original_api_key = os.environ.get("ANGLE_FOUNDRY_API_KEY")

    def tearDown(self) -> None:
        if self.original_api_key is None:
            os.environ.pop("ANGLE_FOUNDRY_API_KEY", None)
        else:
            os.environ["ANGLE_FOUNDRY_API_KEY"] = self.original_api_key
        self.tmp_dir.cleanup()

    def test_load_config_reads_toml_and_env(self) -> None:
        write_config(self.config_path)
        os.environ["ANGLE_FOUNDRY_API_KEY"] = "secret-key"

        config = load_config(self.config_path)

        self.assertEqual(config.topics, ["理财"])
        self.assertEqual(config.directions, ["坑", "盲区", "痛点", "疑问", "跨界话题"])
        self.assertEqual(config.push_provider, "feishu")
        self.assertEqual(config.ai_api_key, "secret-key")

    def test_load_config_requires_api_key(self) -> None:
        write_config(self.config_path)
        os.environ.pop("ANGLE_FOUNDRY_API_KEY", None)

        with self.assertRaisesRegex(ValueError, "ANGLE_FOUNDRY_API_KEY"):
            load_config(self.config_path)

    def test_load_config_validates_constraints(self) -> None:
        cases = [
            ('[]', None, '"feishu"', 60, 2, "topics must be a non-empty list"),
            ('["理财"]', '["坑", "盲区"]', '"feishu"', 60, 2, "directions must be exactly"),
            ('["理财"]', None, '"slack"', 60, 2, "Input should be 'feishu' or 'wecom'"),
            ('["理财"]', None, '"feishu"', 0, 2, "greater than 0"),
            ('["理财"]', None, '"feishu"', 60, -1, "greater than or equal to 0"),
        ]
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
