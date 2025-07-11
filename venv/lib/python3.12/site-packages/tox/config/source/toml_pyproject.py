"""Load from a pyproject.toml file, native format."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Final, Iterator, Mapping, cast

from tox.config.loader.section import Section
from tox.config.loader.toml import TomlLoader
from tox.report import HandledError

from .api import Source

if sys.version_info >= (3, 11):  # pragma: no cover (py311+)
    import tomllib
else:  # pragma: no cover (py311+)
    import tomli as tomllib

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from tox.config.loader.api import Loader, OverrideMap
    from tox.config.sets import CoreConfigSet


class TomlSection(Section):
    SEP: str = "."
    PREFIX: tuple[str, ...]
    ENV: Final[str] = "env"
    RUN_ENV_BASE: Final[str] = "env_run_base"
    PKG_ENV_BASE: Final[str] = "env_pkg_base"

    @classmethod
    def test_env(cls, name: str) -> TomlSection:
        return cls(cls.env_prefix(), name)

    @classmethod
    def env_prefix(cls) -> str:
        return cls.SEP.join((*cls.PREFIX, cls.ENV))

    @classmethod
    def core_prefix(cls) -> str:
        return cls.SEP.join(cls.PREFIX)

    @classmethod
    def package_env_base(cls) -> str:
        return cls.SEP.join((*cls.PREFIX, cls.PKG_ENV_BASE))

    @classmethod
    def run_env_base(cls) -> str:
        return cls.SEP.join((*cls.PREFIX, cls.RUN_ENV_BASE))

    @property
    def keys(self) -> Iterable[str]:
        key = self.key
        keys = key.split(self.SEP) if self.key else []
        if self.PREFIX and len(keys) >= len(self.PREFIX) and tuple(keys[: len(self.PREFIX)]) == self.PREFIX:
            keys = keys[len(self.PREFIX) :]
        return keys


class TomlPyProjectSection(TomlSection):
    PREFIX = ("tool", "tox")


class TomlPyProject(Source):
    """Configuration sourced from a pyproject.toml files."""

    FILENAME = "pyproject.toml"
    _Section: type[TomlSection] = TomlPyProjectSection

    def __init__(self, path: Path) -> None:
        if path.name != self.FILENAME or not path.exists():
            raise ValueError
        with path.open("rb") as file_handler:
            self._content = tomllib.load(file_handler)
        try:
            our_content: Mapping[str, Any] = self._content
            for key in self._Section.PREFIX:
                our_content = our_content[key]
            self._our_content = our_content
        except KeyError as exc:
            raise ValueError(path) from exc
        super().__init__(path)

    def get_core_section(self) -> Section:
        return self._Section(prefix=None, name="")

    def transform_section(self, section: Section) -> Section:
        return self._Section(section.prefix, section.name)

    def get_loader(self, section: Section, override_map: OverrideMap) -> Loader[Any] | None:
        current = self._our_content
        sec = cast("TomlSection", section)
        for key in sec.keys:
            if key in current:
                current = current[key]
            else:
                return None
        if not isinstance(current, Mapping):
            msg = f"{sec.key} must be a table, is {current.__class__.__name__!r}"
            raise HandledError(msg)
        return TomlLoader(
            section=section,
            overrides=override_map.get(section.key, []),
            content=current,
            root_content=self._content,
            unused_exclude={sec.ENV, sec.RUN_ENV_BASE, sec.PKG_ENV_BASE} if section.prefix is None else set(),
        )

    def envs(self, core_conf: CoreConfigSet) -> Iterator[str]:
        yield from core_conf["env_list"]
        yield from [i.key for i in self.sections()]

    def sections(self) -> Iterator[Section]:
        for env_name in self._our_content.get(self._Section.ENV, {}):
            if not isinstance(env_name, str):
                msg = f"Environment key must be string, got {env_name!r}"
                raise HandledError(msg)
            yield self._Section.from_key(env_name)

    def get_base_sections(self, base: list[str], in_section: Section) -> Iterator[Section]:  # noqa: ARG002
        yield from [self._Section.from_key(b) for b in base]

    def get_tox_env_section(self, item: str) -> tuple[Section, list[str], list[str]]:
        return self._Section.test_env(item), [self._Section.run_env_base()], [self._Section.package_env_base()]


__all__ = [
    "TomlPyProject",
]
