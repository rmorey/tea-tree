# ttree

A Rich + Typer powered alternative to `tree` that keeps directory browsing readable by
summarizing noisy folders, colorizing output, and optionally hiding dotfiles.

## Features

- Renders a hierarchical tree with Rich so directories and files are easy to scan.
- Collapses busy directories by summarizing file counts per extension.
- Summarizes large groups of subdirectories with a single line like `42 directories`.
- Ignores dotfiles by default to keep output focused (toggle with `-a/--all`).
- Shows a live progress spinner while crawling large trees in an interactive terminal.

## Installation

This project targets Python 3.13+. With [uv](https://github.com/astral-sh/uv) installed:

```bash
uv sync
```

That will install the dependencies defined in `pyproject.toml`. Alternatively, use any
standard workflow such as `pip install -e .`.

## Usage

After installing (for example with `uv sync` or `pip install -e .`), invoke the CLI:

```
ttree [DIRECTORY] [OPTIONS]
```

Example:

```bash
ttree ~/Developer -m 3 -d 15
```

During development you can also run `uv run ttree` or `python -m ttree` without
installing the console script globally.

Key options:

- `DIRECTORY` (default `.`): root folder to inspect.
- `-m, --max-files-to-list`: show files individually only if their count in a directory
  is less than or equal to this number; otherwise show a summary like
  `5 py, 3 md files`. Set `0` to always summarize.
- `-d, --max-dirs-to-list`: show subdirectories individually only if their count in a
  directory is less than or equal to this number; otherwise show `N directories`.
  Set `0` to only show counts.
- `-a, --all`: include dotfiles in both directories and files. By default, entries that
  start with `.` are skipped.

ttree exits with an error if the provided path does not exist or is not a directory.

## Development

- The CLI lives in `src/ttree/cli.py` (Typer app); `main.py` is a thin wrapper for ad-hoc runs.
- Rich drives both the colored tree output and the optional progress spinner.
- Run `uv run ttree -- --help` or `python -m ttree --help` while iterating.

Contributions and tweaks are welcome—tune the knobs in `src/ttree/cli.py` to customize how
ttree summarizes your filesystem.
