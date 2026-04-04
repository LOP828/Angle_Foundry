# Repository Guidelines

## Project Structure & Module Organization
Source code lives under `app/`. Core infrastructure is in `app/core/`, typed data models in `app/models/`, generation placeholders in `app/generator/`, messaging placeholders in `app/messaging/`, and task orchestration in `app/tasks/`. Runtime configuration files live in `config/`, with `config/config.toml` as the main business config and `config/prompt_template.md` reserved for later prompt work. Tests live in `tests/`. Project docs and planning notes are in `docs/`. Log files should go to `logs/`.

## Build, Test, and Development Commands
Use Python 3.12 and `uv`.

- `uv sync`: install runtime and dev dependencies from `pyproject.toml`
- `uv run pytest`: run the test suite
- `ANGLE_FOUNDRY_API_KEY=your_key uv run python -m app.main --run-once`: load config and perform a one-off startup check
- `python3 -m compileall app tests`: quick syntax validation when dependencies are not installed

## Coding Style & Naming Conventions
Use 4-space indentation and standard Python style. Prefer explicit typing on public functions and Pydantic models for structured data. Module and file names use `snake_case` such as `topic_result.py`; classes use `PascalCase` such as `AppConfig`; functions and variables use `snake_case`. Keep modules focused: config loading stays in `app/core/config.py`, data-only definitions stay in `app/models/`, and side-effecting integrations belong in dedicated modules.

## Testing Guidelines
Primary test framework is `pytest`, with tests stored in `tests/` and named `test_*.py`. Keep tests close to the behavior they verify; for example, configuration validation belongs in `tests/test_config.py`. Cover both valid config loading and failure cases for invalid inputs. Prefer small, isolated tests that write temporary config files instead of mutating shared project files.

## Commit & Pull Request Guidelines
This workspace currently does not include `.git` history, so no repository-specific commit pattern can be inferred. Use short, imperative commit messages such as `Add config validation models` or `Scaffold messaging module`. Pull requests should include a brief summary, the files or modules changed, commands run (`uv run pytest`, `uv sync`), and any remaining risks or unimplemented placeholders.

## Security & Configuration Tips
Do not hardcode secrets in `config/config.toml`. Store the API key in `ANGLE_FOUNDRY_API_KEY`. Validate configuration on startup and fail fast if required fields are missing or invalid. Keep provider values limited to `feishu` or `wecom`.
