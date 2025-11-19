
import os

from rich.text import Text
from rich.tree import Tree

from ttree.cli import build_tree


def _label_text(node: Tree) -> str:
    label = node.label
    if hasattr(label, "plain"):
        return label.plain
    return Text.from_markup(str(label)).plain


def _labels(tree: Tree) -> list[str]:
    labels = []
    for child in tree.children:
        labels.append(_label_text(child))
    return labels


def test_build_tree_shows_symlinks_and_targets(tmp_path) -> None:
    real_file = tmp_path / "real.txt"
    real_file.write_text("content")
    
    link_file = tmp_path / "link.txt"
    os.symlink(real_file, link_file)
    
    tree = Tree("[dir].[/dir]")
    build_tree(
        tmp_path,
        tree,
        max_files_to_list=5,
        max_dirs_to_list=5,
        show_all=False,
    )
    
    # We expect the link to be shown with its target
    # The target path in the output will be the absolute path because os.readlink returns what was passed to symlink?
    # Actually os.readlink returns the exact string stored in the link.
    # In this test we passed an absolute path to os.symlink (real_file is absolute).
    # So we expect "link.txt -> /path/to/real.txt"
    
    labels = _labels(tree)
    assert len(labels) == 2
    assert "real.txt" in labels
    
    # Find the link label
    link_label = next(l for l in labels if l.startswith("link.txt"))
    assert f"link.txt -> {real_file}" == link_label


def test_build_tree_follows_directory_symlink(tmp_path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "inner.txt").write_text("data")

    link_dir = tmp_path / "link"
    os.symlink(real_dir, link_dir)

    tree = Tree("[dir].[/dir]")
    build_tree(
        tmp_path,
        tree,
        max_files_to_list=5,
        max_dirs_to_list=5,
        show_all=False,
    )

    labels = _labels(tree)
    assert any(label.startswith("link") for label in labels)

    link_branch = next(child for child in tree.children if _label_text(child).startswith("link"))
    assert _label_text(link_branch).startswith(f"link -> {real_dir}")
    assert "inner.txt" in _labels(link_branch)
