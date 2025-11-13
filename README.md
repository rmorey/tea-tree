# ttree

ttree is a Rich + Typer powered alternative to `tree` that keeps directory browsing
readable, summarizing noisy folders, colorizing output, and optionally hiding dotfiles.

## Features

- Rich renders a hierarchical tree with coloring for directories, files, and summaries.
- Crowded directories are collapsed: file clusters become summaries like `5 py, 3 md files`
  and subdirectories collapse to `N directories`.
- Dotfiles stay hidden unless you opt in with `-a/--all`.
- A live progress spinner appears when scanning large trees on a TTY.
- `-V/--version` prints the installed version for quick diagnostics.

## Installation

Requires Python 3.11+.

From PyPI:

```bash
pip install tea-tree
```

For local development, install via [uv](https://github.com/astral-sh/uv):

```bash
uv sync --extra dev
```

or use `pip install -e .[dev]`. After installation the `ttree` console script is available
on your PATH.

## Usage

```
ttree [DIRECTORY] [OPTIONS]
```

Common examples:

```bash
# summarize files once there are more than 2 siblings
ttree ~/Developer -m 2

# include dotfiles and show fewer subdirectories before collapsing
ttree src -a -d 5

# print version information immediately
ttree -V
```

During development, `uv run ttree -- --help` or `python -m ttree` behave the same without
installing the entry point.

### Key options

- `DIRECTORY` (default `.`): root folder to inspect.
- `-m, --max-files-to-list`: maximum files to display individually before summarizing.
  Set to `0` to always show summaries.
- `-d, --max-dirs-to-list`: maximum subdirectories to list before using `N directories`.
  Set to `0` to only emit counts.
- `-a, --all`: include entries starting with `.`.

## Example Output

```
$ ttree demo -m 2 -d 3
demo
├── api
│   ├── handlers
│   └── models
├── docs
│   └── 3 directories
├── scripts
│   └── 4 py, 1 sh files
└── tests
    ├── unit
    └── 5 directories
```

The actual CLI uses color and dimmed summaries via Rich; the example above shows the
structure you can expect.

## Development

- CLI implementation: `src/ttree/cli.py`; helpers live nearby. `main.py` is a lightweight
  wrapper for executing the app without installation.
- Run tests via `pytest`. Fixtures cover directory summaries, dotfile behavior, permission
  errors, and Typer command invocations.
- Build distributables with `uv build`; the project uses the `uv_build` backend.

Contributions are welcome—tune the thresholds or output styles in `src/ttree/cli.py` and
update the tests to keep coverage high.

## Publishing to PyPI

1. Bump `version` in `pyproject.toml` and update the changelog/README as needed.
2. Install dependencies (`uv sync --extra dev`) and run `pytest`.
3. Build artifacts: `uv build` (creates `dist/tea_tree-<version>.whl` and `.tar.gz`).
4. Publish with a PyPI token: `UV_PYPI_TOKEN=... uv publish --token "$UV_PYPI_TOKEN"`.

The published distribution name is `tea-tree`, while the installed CLI remains `ttree`.
