from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from mkdocs.structure.nav import Section


class StructureItem(metaclass=abc.ABCMeta):
    """An item in MkDocs structure - see concrete subclasses Section, Page or Link."""

    @abc.abstractmethod
    def __init__(self):
        ...

    parent: Section | None = None
    """The immediate parent of the item in the site navigation. `None` if it's at the top level."""

    @property
    def is_top_level(self) -> bool:
        return self.parent is None

    title: str | None
    is_section: bool = False
    is_page: bool = False
    is_link: bool = False

    @property
    def ancestors(self) -> Iterable[StructureItem]:
        if self.parent is None:
            return []
        return [self.parent, *self.parent.ancestors]

    def _indent_print(self, depth: int = 0) -> str:
        return ('    ' * depth) + repr(self)
