"""
ttree: a tree-like directory listing using rich + typer.

- Directories are shown as a hierarchy, unless there are "too many" siblings.
- Files are either:
  - listed individually if their count in a directory <= max_files_to_list
  - summarized as "N files" if their count > max_files_to_list, grouped by type

- Directories are either:
  - listed individually if their count in a directory <= max_dirs_to_list
  - summarized as "N directories" if their count > max_dirs_to_list

- By default, dotfiles (files or dirs starting with '.') are ignored. Use -a/--all to show them.
"""

from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass
from importlib import metadata as _metadata
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore

import typer
from rich.console import Console
from rich.theme import Theme
from rich.tree import Tree

__all__ = ["app"]

app = typer.Typer(add_completion=False)

_DIST_NAME = "tea-tree"

try:
    __version__ = _metadata.version(_DIST_NAME)
except _metadata.PackageNotFoundError:  # pragma: no cover - local dev editable installs
    if tomllib is not None:
        try:
            project_root = Path(__file__).resolve().parents[2]
            pyproject = project_root / "pyproject.toml"
            data = tomllib.loads(pyproject.read_text())
            __version__ = data["project"]["version"]
        except Exception:
            __version__ = "0.0.0"
    else:
        __version__ = "0.0.0"

theme = Theme(
    {
        "dir": "bold blue",
        "file": "green",
        "summary": "dim",
        "error": "bold red",
    }
)
console = Console(theme=theme)


@dataclass
class CrawlStats:
    directories: int = 0
    files: int = 0


def get_file_type(filename: str) -> str:
    """
    Returns the lowercase file extension (without leading dot),
    or 'no extension' if none found.
    """
    p = Path(filename)
    ext = p.suffix.lower()
    if ext:
        return ext[1:]  # without leading '.'
    else:
        return "no extension"


def summarize_types(files: Iterable[os.DirEntry]) -> str:
    """
    Count types in files and produce a summary string like '4 py, 2 txt, 1 no extension files'
    """
    types = [get_file_type(f.name) for f in files]
    counts = Counter(types)
    parts = []
    for ext, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        label = f"{ext}" if ext != "no extension" else "no extension"
        parts.append(f"{count} {label}")
    noun = "file" if sum(counts.values()) == 1 else "files"
    return f"{', '.join(parts)} {noun}"


def update_status(status, root_label: str, stats: CrawlStats) -> None:
    """Update the spinner text with current directory/file counts."""
    if status is None:
        return
    d = stats.directories
    f = stats.files
    d_noun = "directory" if d == 1 else "directories"
    f_noun = "file" if f == 1 else "files"
    status.update(
        f"[summary]Scanning {root_label}... "
        f"({d} {d_noun}, {f} {f_noun})[/summary]"
    )


def build_tree(
    path: Path,
    tree: Tree,
    max_files_to_list: int,
    max_dirs_to_list: int,
    show_all: bool,
    stats: CrawlStats | None = None,
    status=None,
    root_label: str | None = None,
) -> None:
    """
    Recursively build the tree for `path` into the given rich Tree node.

    If show_all is False, dotfiles (files or dirs starting with '.') are ignored.
    """
    try:
        with os.scandir(path) as it:
            if show_all:
                entries = list(it)
            else:
                entries = [e for e in it if not e.name.startswith(".")]
    except PermissionError:
        tree.add("[error]permission denied[/error]")
        return

    dirs = [e for e in entries if e.is_dir(follow_symlinks=False)]
    files = [e for e in entries if e.is_file(follow_symlinks=False)]

    dirs.sort(key=lambda e: e.name)
    files.sort(key=lambda e: e.name)

    if stats is not None:
        stats.directories += len(dirs)
        stats.files += len(files)
        if status is not None and root_label is not None:
            update_status(status, root_label, stats)

    num_dirs = len(dirs)
    if num_dirs:
        if num_dirs <= max_dirs_to_list:
            for d in dirs:
                branch = tree.add(f"[dir]{d.name}[/dir]")
                build_tree(
                    Path(d.path),
                    branch,
                    max_files_to_list=max_files_to_list,
                    max_dirs_to_list=max_dirs_to_list,
                    show_all=show_all,
                    stats=stats,
                    status=status,
                    root_label=root_label,
                )
        else:
            noun = "directory" if num_dirs == 1 else "directories"
            tree.add(f"[summary]{num_dirs} {noun}[/summary]")

    num_files = len(files)
    if not num_files:
        return

    if num_files <= max_files_to_list:
        for f in files:
            tree.add(f"[file]{f.name}[/file]")
    else:
        summary = summarize_types(files)
        tree.add(f"[summary]{summary}[/summary]")


@app.command()
def main(
    directory: str = typer.Argument(
        ".",
        help="Root directory (default: current directory).",
    ),
    max_files_to_list: int = typer.Option(
        1,
        "-m",
        "--max-files-to-list",
        min=0,
        help=(
            "Maximum number of files to list individually per directory. "
            "If a directory has more files than this, show a summary by type like "
            "'4 py, 2 txt files' instead. Default: 1"
        ),
    ),
    max_dirs_to_list: int = typer.Option(
        20,
        "-d",
        "--max-dirs-to-list",
        min=0,
        help=(
            "Maximum number of subdirectories to list individually per directory. "
            "If a directory has more subdirectories than this, show 'N directories' "
            "instead of listing them. Default: 20"
        ),
    ),
    show_all: bool = typer.Option(
        False,
        "-a",
        "--all",
        help="Include dotfiles (files/dirs starting with '.') in the listing.",
    ),
    version: bool = typer.Option(
        False,
        "-V",
        "--version",
        help="Show ttree version and exit.",
        is_eager=True,
    ),
) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit()

    root_path = Path(directory)

    if not root_path.exists():
        console.print(f"[error]Path does not exist:[/error] {directory}")
        raise typer.Exit(code=1)

    if not root_path.is_dir():
        console.print(f"[error]Not a directory:[/error] {directory}")
        raise typer.Exit(code=1)

    if directory in (".", ""):
        display_root = "."
    else:
        display_root = directory.rstrip("/")

    root_tree = Tree(f"[dir]{display_root}[/dir]")
    stats = CrawlStats()

    use_spinner = console.is_terminal
    if use_spinner:
        with console.status(
            f"[summary]Scanning {display_root}... (0 directories, 0 files)[/summary]",
            spinner="dots",
        ) as status:
            build_tree(
                root_path,
                root_tree,
                max_files_to_list=max_files_to_list,
                max_dirs_to_list=max_dirs_to_list,
                show_all=show_all,
                stats=stats,
                status=status,
                root_label=display_root,
            )
    else:
        build_tree(
            root_path,
            root_tree,
            max_files_to_list=max_files_to_list,
            max_dirs_to_list=max_dirs_to_list,
            show_all=show_all,
            stats=stats,
            status=None,
            root_label=display_root,
        )

    console.print(root_tree)
