"""Public package surface for ttree."""

from importlib import metadata as _metadata
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore

from .cli import app

__all__ = ["app", "__version__"]

_DIST_NAME = "tea-tree"

try:  # pragma: no cover - during development package metadata may be unavailable
    __version__ = _metadata.version(_DIST_NAME)
except _metadata.PackageNotFoundError:  # pragma: no cover
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
