# Manual Verification

## 1. Real `--run-once` Verification

Required environment variables:

- `ANGLE_FOUNDRY_API_KEY`
- `FEISHU_WEBHOOK`
- `ANGLE_FOUNDRY_AI_BASE_URL`
- `ANGLE_FOUNDRY_AI_MODEL`
- Optional: `ANGLE_FOUNDRY_AI_TIMEOUT_SECONDS`, `ANGLE_FOUNDRY_AI_MAX_RETRIES`

Linux/macOS example:

```bash
export ANGLE_FOUNDRY_API_KEY="..."
export FEISHU_WEBHOOK="..."
export ANGLE_FOUNDRY_AI_BASE_URL="https://your-ai-endpoint/v1"
export ANGLE_FOUNDRY_AI_MODEL="your-model"
UV_CACHE_DIR=.uv-cache uv run python -m app.main --run-once
```

PowerShell example:

```powershell
$env:ANGLE_FOUNDRY_API_KEY = "..."
$env:FEISHU_WEBHOOK = "..."
$env:ANGLE_FOUNDRY_AI_BASE_URL = "https://your-ai-endpoint/v1"
$env:ANGLE_FOUNDRY_AI_MODEL = "your-model"
$env:UV_CACHE_DIR = ".uv-cache"
uv run python -m app.main --run-once
```

Expected output:

- Console log contains `Daily topic task started`
- Each topic logs either `processed successfully` or a failure stack trace
- Final log contains `Run-once summary: {...}`
- Exit code is `0` when all topics succeed, otherwise `1`

Log file:

- `logs/angle_foundry.log`

Failure triage:

- Config error at startup: check `config/config.toml` and `ANGLE_FOUNDRY_API_KEY`
- AI request failure: check `ANGLE_FOUNDRY_AI_BASE_URL`, model, API key, proxy, TLS
- Feishu send failure: check `FEISHU_WEBHOOK` and returned platform code
- Validation failure: inspect raw AI text and the logged error in the summary

## 2. Minimal Scheduler Verification

Goal: prove default mode can trigger one scheduled execution.

1. Copy `config/config.toml` to a temporary file.
2. Change `[schedule].cron` to a near-future value, for example one minute later.
3. Limit `[generator].topics` to one topic to reduce noise.
4. Start the app without `--run-once`.

Example:

```bash
UV_CACHE_DIR=.uv-cache uv run python -m app.main --config config/config.smoke.toml
```

Expected result:

- Console shows `Scheduler started with cron '...'`
- At the target minute, one task run appears in console and `logs/angle_foundry.log`
- After one successful trigger, stop the process manually with `Ctrl+C`
