"""Public package surface for ttree."""

from importlib import metadata as _metadata

from .cli import app

__all__ = ["app", "__version__"]

try:  # pragma: no cover - during development package metadata is unavailable
    __version__ = _metadata.version("ttree")
except _metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
