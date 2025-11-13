from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from rich.text import Text
from rich.tree import Tree
from typer.testing import CliRunner

import ttree.cli as cli_module
from ttree import __version__
from ttree.cli import app, build_tree, configure_console, get_file_type, summarize_types

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


def test_env_requests_no_color_handles_env(monkeypatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert cli_module._env_requests_no_color() is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert cli_module._env_requests_no_color() is True
    monkeypatch.setenv("NO_COLOR", "0")
    assert cli_module._env_requests_no_color() is False


def test_configure_console_toggles_color() -> None:
    configure_console(True)
    assert cli_module.console.no_color is True
    configure_console(False)
    assert cli_module.console.no_color is False


def test_cli_no_color_option_disables_colors() -> None:
    result = runner.invoke(app, ["--no-color", "-V"])
    assert result.exit_code == 0
    assert cli_module.console.no_color is True
    configure_console(False)


def test_cli_respects_no_color_env(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert cli_module.console.no_color is True
    monkeypatch.delenv("NO_COLOR", raising=False)
    configure_console(False)


def test_get_file_type_handles_extensions_and_missing() -> None:
    assert get_file_type("notes.md") == "md"
    assert get_file_type("archive.tar.gz") == "gz"
    assert get_file_type("LICENSE") == "no extension"


def test_summarize_types_lists_unique_types_before_group_counts() -> None:
    files = [
        SimpleNamespace(name="a.py"),
        SimpleNamespace(name="b.PY"),
        SimpleNamespace(name="c.txt"),
        SimpleNamespace(name="README"),
    ]
    assert (
        summarize_types(files)
        == "[file]README[/file], [file]c.txt[/file], [summary]2 py[/summary] [summary]files[/summary]"
    )


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

    assert _labels(tree) == ["README, 2 py files"]


def test_summarize_types_includes_filenames_for_single_extension_groups() -> None:
    entries = [
        SimpleNamespace(name="report.log"),
        SimpleNamespace(name="notes.md"),
        SimpleNamespace(name="image.JPG"),
        SimpleNamespace(name="script.sh"),
    ]
    expected = (
        "[file]image.JPG[/file], "
        "[file]notes.md[/file], "
        "[file]report.log[/file], "
        "[file]script.sh[/file] [summary]files[/summary]"
    )
    assert summarize_types(entries) == expected


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
