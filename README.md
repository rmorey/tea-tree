# ttree 🍵-∂🌳

ttree is an alternative to `tree` that keeps directory browsing
readable, summarizing noisy folders, colorizing output, and optionally hiding dotfiles.

## Features

- Renders a hierarchical tree with coloring for directories, files, and summaries.
- Crowded directories are collapsed: file clusters become summaries like `5 py, 3 md files`
  and subdirectories collapse to `N directories`.
- Dotfiles stay hidden unless you opt in with `-a/--all`.
- Need plain output for CI logs? pass `--no-color` or set `NO_COLOR=1`.
- A live progress spinner appears when scanning large trees on a TTY.

## Installation

Requires Python 3.11+.

With uv:

```bash
uv tool install tea-tree
```

With pip:

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
- `--no-color`: disable Rich colors (equivalent to exporting `NO_COLOR=1`).

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

_WIP, mostly written by GPT-5-Codex_