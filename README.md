# Angle Foundry

Minimal daily topic generation and push tool. Current scope is a single-process backend that reads config, generates topic ideas through an AI endpoint, validates structured output, formats a text message, and pushes it to Feishu.

## Requirements

- Python 3.12
- `uv`

## Install uv

If `uv` is not installed locally:

```bash
python3 -m pip install --user --break-system-packages uv
export PATH="$HOME/.local/bin:$PATH"
```

## Install

```bash
uv sync
```

## Run tests

```bash
uv run pytest
```

## Configuration

Main config file:

- `config/config.toml`

Required environment variable:

- `ANGLE_FOUNDRY_API_KEY`

Real delivery also needs:

- `ANGLE_FOUNDRY_AI_BASE_URL`
- `ANGLE_FOUNDRY_AI_MODEL`
- `FEISHU_WEBHOOK`

## Run Once

```bash
export ANGLE_FOUNDRY_API_KEY="your-api-key"
export ANGLE_FOUNDRY_AI_BASE_URL="https://your-ai-endpoint/v1"
export ANGLE_FOUNDRY_AI_MODEL="your-model"
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook"
UV_CACHE_DIR=.uv-cache uv run python -m app.main --run-once
```

Expected result:

- Console prints per-topic progress and a final `Run-once summary`
- Log file is written to `logs/angle_foundry.log`
- Exit code is `0` on full success, `1` if any topic fails

## Default Scheduler Mode

```bash
export ANGLE_FOUNDRY_API_KEY="your-api-key"
export ANGLE_FOUNDRY_AI_BASE_URL="https://your-ai-endpoint/v1"
export ANGLE_FOUNDRY_AI_MODEL="your-model"
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook"
UV_CACHE_DIR=.uv-cache uv run python -m app.main
```

The app starts a blocking scheduler and waits for the configured cron to trigger `daily_topic_task`.

## Real Smoke Test

For the smaller end-to-end check that sends one handcrafted `TopicResult`, run:

```bash
export ANGLE_FOUNDRY_AI_BASE_URL="https://your-ai-endpoint/v1"
export ANGLE_FOUNDRY_AI_MODEL="your-model"
export ANGLE_FOUNDRY_API_KEY="your-api-key"
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook"
UV_CACHE_DIR=.uv-cache uv run python scripts/smoke_real_delivery.py
```

## Acceptance Checklist

1. `uv run pytest` passes.
2. `python -m app.main --run-once` prints a summary and writes `logs/angle_foundry.log`.
3. The smoke script can fetch one AI response and send one Feishu text message.
4. Default scheduler mode logs `Scheduler started with cron '...'`.

## Manual Verification

Detailed manual verification and scheduler proof steps are documented in [manual-verification.md](/mnt/d/project/Angle_Foundry/docs/manual-verification.md).
