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


def _env_requests_no_color() -> bool:
    """Return True if the NO_COLOR environment variable disables color output."""
    value = os.environ.get("NO_COLOR")
    if value is None:
        return False
    return value not in ("", "0")


console = Console(theme=theme, no_color=_env_requests_no_color())


def configure_console(disable_color: bool) -> None:
    """Reinitialize the global console with the requested color setting."""
    global console
    console = Console(theme=theme, no_color=disable_color)


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
    Count types in files and produce a summary string with markup.

    - Unique extensions are listed by filename in `[file]` markup so they stay green.
    - Shared extensions are grouped and wrapped in `[summary]` so they stay dim.
    """
    file_entries = list(files)
    if not file_entries:
        return "[summary]0 files[/summary]"

    file_infos = [(entry.name, get_file_type(entry.name)) for entry in file_entries]
    file_infos.sort(key=lambda info: info[0])

    counts = Counter(ftype for _, ftype in file_infos)

    singletons = [
        f"[file]{name}[/file]" for name, ftype in file_infos if counts[ftype] == 1
    ]
    grouped = []
    for ext, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        if count == 1:
            continue
        label = f"{ext}" if ext != "no extension" else "no extension"
        grouped.append(f"[summary]{count} {label}[/summary]")

    parts = singletons + grouped
    noun = "file" if sum(counts.values()) == 1 else "files"
    noun_markup = f"[summary]{noun}[/summary]"
    if not parts:
        return noun_markup

    return f"{', '.join(parts)} {noun_markup}"


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
    seen: set[tuple[int, int]] | None = None,
) -> None:
    """
    Recursively build the tree for `path` into the given rich Tree node.

    If show_all is False, dotfiles (files or dirs starting with '.') are ignored.
    """
    if seen is None:
        seen = set()
    try:
        stat_result = os.stat(path, follow_symlinks=True)
        seen.add((stat_result.st_ino, stat_result.st_dev))
    except OSError:
        pass

    try:
        with os.scandir(path) as it:
            if show_all:
                entries = list(it)
            else:
                entries = [e for e in it if not e.name.startswith(".")]
    except PermissionError:
        tree.add("[error]permission denied[/error]")
        return

    dirs: list[os.DirEntry] = []
    files: list[os.DirEntry] = []

    for entry in entries:
        try:
            if entry.is_dir(follow_symlinks=True):
                dirs.append(entry)
                continue
        except OSError:
            pass

        try:
            if entry.is_file(follow_symlinks=False) or entry.is_symlink():
                files.append(entry)
        except OSError:
            files.append(entry)

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
                dir_label = f"[dir]{d.name}[/dir]"
                if d.is_symlink():
                    try:
                        target = os.readlink(d.path)
                        dir_label = f"{dir_label} -> {target}"
                    except OSError:
                        dir_label = f"{dir_label} -> [error]?[/error]"

                branch = tree.add(dir_label)

                inode: tuple[int, int] | None = None
                try:
                    stat_result = os.stat(d.path, follow_symlinks=True)
                    inode = (stat_result.st_ino, stat_result.st_dev)
                except OSError:
                    pass

                # Prevent infinite recursion when a directory is reachable via multiple paths.
                if inode is not None and inode in seen:
                    continue

                if inode is not None:
                    seen.add(inode)

                build_tree(
                    Path(d.path),
                    branch,
                    max_files_to_list=max_files_to_list,
                    max_dirs_to_list=max_dirs_to_list,
                    show_all=show_all,
                    stats=stats,
                    status=status,
                    root_label=root_label,
                    seen=seen,
                )
        else:
            noun = "directory" if num_dirs == 1 else "directories"
            tree.add(f"[summary]{num_dirs} {noun}[/summary]")

    num_files = len(files)
    if not num_files:
        return

    if num_files <= max_files_to_list:
        for f in files:
            if f.is_symlink():
                try:
                    target = os.readlink(f.path)
                    tree.add(f"[file]{f.name}[/file] -> {target}")
                except OSError:
                    tree.add(f"[file]{f.name}[/file] -> [error]?[/error]")
            else:
                tree.add(f"[file]{f.name}[/file]")
    else:
        summary = summarize_types(files)
        tree.add(summary)


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
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output (same as setting NO_COLOR=1).",
    ),
    version: bool = typer.Option(
        False,
        "-V",
        "--version",
        help="Show ttree version and exit.",
        is_eager=True,
    ),
) -> None:
    disable_color = no_color or _env_requests_no_color()
    configure_console(disable_color)

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
