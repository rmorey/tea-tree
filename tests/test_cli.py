from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from rich.text import Text
from rich.tree import Tree
from typer.testing import CliRunner

import ttree.cli as cli_module
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


def test_build_tree_summarizes_files_when_limit_exceeded(tmp_path) -> None:
    (tmp_path / "alpha.py").write_text("")
    (tmp_path / "beta.PY").write_text("")
    (tmp_path / "README").write_text("")

    tree = Tree("[dir].[/dir]")
    build_tree(
        tmp_path,
        tree,
        max_files_to_list=1,
        max_dirs_to_list=5,
        show_all=True,
    )

    assert _labels(tree) == ["2 py, 1 no extension files"]


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


def test_build_tree_handles_permission_error(monkeypatch, tmp_path) -> None:
    real_scandir = cli_module.os.scandir

    def fake_scandir(path):
        if Path(path) == tmp_path:
            raise PermissionError
        return real_scandir(path)

    monkeypatch.setattr(cli_module.os, "scandir", fake_scandir)

    tree = Tree("[dir].[/dir]")
    build_tree(
        tmp_path,
        tree,
        max_files_to_list=5,
        max_dirs_to_list=5,
        show_all=True,
    )

    assert _labels(tree) == ["permission denied"]


def test_version_flag() -> None:
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert __version__ in result.stdout.strip()


def test_cli_errors_on_missing_path(tmp_path) -> None:
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(app, [str(missing)])
    assert result.exit_code == 1
    assert "Path does not exist" in result.stdout
