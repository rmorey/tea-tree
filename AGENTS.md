# Repository Guidelines

## Project Structure & Module Organization
- Source lives under `src/ttree`; `cli.py` hosts the Typer app and Rich rendering, while `__init__.py` exposes `app`/`__version__`.
- Tests reside in `tests/`, mirroring CLI behaviors with pytest and Typer’s `CliRunner`.
- `main.py` is a thin wrapper for local runs; packaging metadata is in `pyproject.toml`.

## Build, Test, and Development Commands
- `uv sync` — install dependencies declared in `pyproject.toml`.
- `uv run ttree -- [PATH]` or `ttree [PATH]` — execute the CLI against a directory.
- `source .venv/bin/activate && pytest` — run the full test suite.
- `uv build` — produce wheel and sdist via the uv build backend.

## Coding Style & Naming Conventions
- Python 3.11+ code with standard 4-space indentation and type hints.
- Keep CLI logic in Typer command functions; helper utilities belong near consumers.
- Rich markup strings follow `[style]text[/style]`; prefer lower-case summaries for predictable comparisons.
- Stick to snake_case for module-level helpers and CLI options.

## Testing Guidelines
- Framework: pytest with fixtures (`tmp_path`, `monkeypatch`) and Typer’s `CliRunner`.
- Mirror CLI scenarios: directory summaries, dotfile toggles, permission errors, and version flag behavior.
- Add new tests in `tests/test_cli.py`, naming them `test_<behavior>`; ensure deterministic assertions (e.g., strip Rich markup before comparing).
- Run `pytest` before commits; keep coverage high for tree-building branches.

## Commit & Pull Request Guidelines
- Use concise, imperative commit messages (e.g., “Add file summary tests”, “Improve CLI error handling”), matching existing history.
- PRs should describe motivation, list major code changes, and mention testing (`pytest`) results; include screenshots or sample CLI output when visual behavior changes.

## Security & Configuration Tips
- Avoid committing secrets or OS cruft; `.gitignore` already excludes `.venv/`, `.pytest_cache/`, and `.DS_Store`.
- When testing permission errors, rely on monkeypatching `os.scandir` rather than modifying filesystem ACLs to keep runs deterministic.
