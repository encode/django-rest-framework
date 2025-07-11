from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Union

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 10):  # pragma: no cover (py310+)
        from typing import TypeAlias
    else:  # pragma: no cover (py310+)
        from typing_extensions import TypeAlias

TomlTypes: TypeAlias = Union[Dict[str, "TomlTypes"], List["TomlTypes"], str, int, float, bool, None]

__all__ = [
    "TomlTypes",
]
