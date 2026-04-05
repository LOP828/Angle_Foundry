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

## 1.1 History Dedup Verification Notes

History file:

- Successful pushes are appended to `logs/topic_history.jsonl`
- Each JSONL record keeps only `date`, `topic`, `direction`, `title`

How `recent_titles` takes effect:

- At task start, the app loads titles from the most recent 1 day of `logs/topic_history.jsonl`
- Those titles are passed into `prompt_builder` as `recent_titles`, so the prompt explicitly tells the model not to regenerate them
- The same `recent_titles` list is also passed into the validator for exact history duplicate checks
- After a successful push, the newly sent titles are appended back into `logs/topic_history.jsonl`

Meaning of `[history_duplicate]`:

- This validator error means a generated title matches a recent history title after normalization
- Normalization currently trims leading and trailing spaces, normalizes Chinese and English punctuation, and lowercases before comparison
- When this error appears, the task treats it as a validation failure and retries once

How to do a next-day `--run-once` verification:

1. Run one successful `--run-once` execution and confirm `logs/topic_history.jsonl` was created.
2. Open `logs/topic_history.jsonl` and keep one known title as yesterday's record by changing its `date` field to the previous calendar day.
3. Run `UV_CACHE_DIR=.uv-cache uv run python -m app.main --run-once` again with the same topic configuration.
4. Confirm the prompt path uses recent history and the run does not reuse the seeded title.
5. If the first generation still hits the same title, confirm logs show a validation failure containing `[history_duplicate]` and then one retry.
6. Confirm the final successful titles are appended as new JSONL lines in `logs/topic_history.jsonl`.

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
