from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Iterator, List, Mapping, TypeVar, cast

from tox.config.loader.api import ConfigLoadArgs, Loader, Override
from tox.config.set_env import SetEnv
from tox.config.types import Command, EnvList
from tox.report import HandledError

from ._api import TomlTypes
from ._replace import Unroll
from ._validate import validate

if TYPE_CHECKING:
    from tox.config.loader.convert import Factory
    from tox.config.loader.section import Section
    from tox.config.main import Config

_T = TypeVar("_T")
_V = TypeVar("_V")


class TomlLoader(Loader[TomlTypes]):
    """Load configuration from a pyproject.toml file."""

    def __init__(
        self,
        section: Section,
        overrides: list[Override],
        content: Mapping[str, TomlTypes],
        root_content: Mapping[str, TomlTypes],
        unused_exclude: set[str],
    ) -> None:
        self.content = content
        self._root_content = root_content
        self._unused_exclude = unused_exclude
        super().__init__(section, overrides)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.section.name}, {self.content!r})"

    def load_raw(self, key: str, conf: Config | None, env_name: str | None) -> TomlTypes:  # noqa: ARG002
        return self.content[key]

    def load_raw_from_root(self, path: str) -> TomlTypes:
        current = cast("TomlTypes", self._root_content)
        for key in path.split(self.section.SEP):
            if isinstance(current, dict):
                current = current[key]
            else:
                msg = f"Failed to load key {key} as not dictionary {current!r}"
                logging.warning(msg)
                raise KeyError(msg)
        return current

    def build(  # noqa: PLR0913
        self,
        key: str,  # noqa: ARG002
        of_type: type[_T],
        factory: Factory[_T],
        conf: Config | None,
        raw: TomlTypes,
        args: ConfigLoadArgs,
    ) -> _T:
        exploded = Unroll(conf=conf, loader=self, args=args)(raw)
        result = self.to(exploded, of_type, factory)
        if inspect.isclass(of_type) and issubclass(of_type, SetEnv):
            result.use_replacer(lambda c, s: c, args=args)  # type: ignore[attr-defined] # noqa: ARG005
        return result

    def found_keys(self) -> set[str]:
        return set(self.content.keys()) - self._unused_exclude

    @staticmethod
    def to_str(value: TomlTypes) -> str:
        return validate(value, str)  # type: ignore[return-value] # no mypy support

    @staticmethod
    def to_bool(value: TomlTypes) -> bool:
        return validate(value, bool)

    @staticmethod
    def to_list(value: TomlTypes, of_type: type[_T]) -> Iterator[_T]:
        of = List[of_type]  # type: ignore[valid-type] # no mypy support
        return iter(validate(value, of))  # type: ignore[call-overload,no-any-return]

    @staticmethod
    def to_set(value: TomlTypes, of_type: type[_T]) -> Iterator[_T]:
        of = List[of_type]  # type: ignore[valid-type] # no mypy support
        return iter(validate(value, of))  # type: ignore[call-overload,no-any-return]

    @staticmethod
    def to_dict(value: TomlTypes, of_type: tuple[type[_T], type[_V]]) -> Iterator[tuple[_T, _V]]:
        of = Dict[of_type[0], of_type[1]]  # type: ignore[valid-type] # no mypy support
        return validate(value, of).items()  # type: ignore[attr-defined,no-any-return]

    @staticmethod
    def to_path(value: TomlTypes) -> Path:
        return Path(TomlLoader.to_str(value))

    @staticmethod
    def to_command(value: TomlTypes) -> Command | None:
        if value:
            return Command(args=cast("List[str]", value))  # validated during load in _ensure_type_correct
        return None

    @staticmethod
    def to_env_list(value: TomlTypes) -> EnvList:
        return EnvList(envs=list(TomlLoader.to_list(value, str)))


__all__ = [
    "HandledError",
    "TomlLoader",
]
