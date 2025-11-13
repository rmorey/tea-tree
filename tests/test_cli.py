from __future__ import annotations

from types import SimpleNamespace

from rich.text import Text
from rich.tree import Tree
from typer.testing import CliRunner

from ttree import __version__
from ttree.cli import app, build_tree, get_file_type, summarize_types

runner = CliRunner()


def _labels(tree: Tree) -> list[str]:
    labels = []
    for child in tree.children:
        label = child.label
        if hasattr(label, "plain"):
            labels.append(label.plain)
        else:
            labels.append(Text.from_markup(str(label)).plain)
    return labels


def test_get_file_type_handles_extensions_and_missing() -> None:
    assert get_file_type("notes.md") == "md"
    assert get_file_type("archive.tar.gz") == "gz"
    assert get_file_type("LICENSE") == "no extension"


def test_summarize_types_orders_by_frequency_then_name() -> None:
    files = [
        SimpleNamespace(name="a.py"),
        SimpleNamespace(name="b.PY"),
        SimpleNamespace(name="c.txt"),
        SimpleNamespace(name="README"),
    ]
    assert summarize_types(files) == "2 py, 1 no extension, 1 txt files"


def test_build_tree_summarizes_directory_counts(tmp_path) -> None:
    for name in ("alpha", "beta", "gamma"):
        (tmp_path / name).mkdir()

    tree = Tree("[dir].[/dir]")
    build_tree(
        tmp_path,
        tree,
        max_files_to_list=5,
        max_dirs_to_list=2,
        show_all=False,
    )

    assert _labels(tree) == ["3 directories"]


def test_build_tree_honors_show_all_flag(tmp_path) -> None:
    (tmp_path / ".hidden.txt").write_text("secret")

    tree = Tree("[dir].[/dir]")
    build_tree(
        tmp_path,
        tree,
        max_files_to_list=5,
        max_dirs_to_list=5,
        show_all=False,
    )
    assert _labels(tree) == []

    tree = Tree("[dir].[/dir]")
    build_tree(
        tmp_path,
        tree,
        max_files_to_list=5,
        max_dirs_to_list=5,
        show_all=True,
    )
    assert _labels(tree) == [".hidden.txt"]


def test_version_flag() -> None:
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert __version__ in result.stdout.strip()
