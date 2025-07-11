"""Load from a tox.toml file."""

from __future__ import annotations

from .toml_pyproject import TomlPyProject, TomlSection


class TomlToxSection(TomlSection):
    PREFIX = ()


class TomlTox(TomlPyProject):
    """Configuration sourced from a pyproject.toml files."""

    FILENAME = "tox.toml"
    _Section = TomlToxSection


__all__ = [
    "TomlTox",
]
