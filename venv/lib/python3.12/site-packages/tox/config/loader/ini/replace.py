"""Apply value substitution (replacement) on tox strings."""

from __future__ import annotations

import re
from configparser import SectionProxy
from functools import lru_cache
from typing import TYPE_CHECKING, Iterator, Pattern

from tox.config.loader.replacer import ReplaceReference
from tox.config.loader.stringify import stringify

if TYPE_CHECKING:
    from tox.config.loader.api import ConfigLoadArgs
    from tox.config.loader.ini import IniLoader
    from tox.config.main import Config
    from tox.config.sets import ConfigSet


class ReplaceReferenceIni(ReplaceReference):
    def __init__(self, conf: Config, loader: IniLoader) -> None:
        self.conf = conf
        self.loader = loader

    def __call__(self, value: str, conf_args: ConfigLoadArgs) -> str | None:  # noqa: C901
        # a return value of None indicates could not replace
        pattern = _replace_ref(self.loader.section.prefix or self.loader.section.name)
        match = pattern.match(value)
        if match:
            settings = match.groupdict()

            key = settings["key"]
            if settings["section"] is None and settings["full_env"]:
                settings["section"] = settings["full_env"]

            exception: Exception | None = None
            try:
                for src in self._config_value_sources(settings["env"], settings["section"], conf_args.env_name):
                    try:
                        if isinstance(src, SectionProxy):
                            return self.loader.process_raw(self.conf, conf_args.env_name, src[key])
                        value = src.load(key, conf_args.chain)
                    except KeyError as exc:  # if fails, keep trying maybe another source can satisfy # noqa: PERF203
                        exception = exc
                    else:
                        as_str, _ = stringify(value)
                        return as_str.replace("#", r"\#")  # escape comment characters as these will be stripped
            except Exception as exc:  # noqa: BLE001
                exception = exc
            if exception is not None:
                if isinstance(exception, KeyError):  # if the lookup failed replace - else keep
                    default = settings["default"]
                    if default is not None:
                        return default
                    # we cannot raise here as that would mean users could not write factorials:
                    #   depends = {py39,py38}-{,b}
                else:
                    raise exception
        return None

    def _config_value_sources(
        self, env: str | None, section: str | None, current_env: str | None
    ) -> Iterator[SectionProxy | ConfigSet]:
        # if we have an env name specified take only from there
        if env is not None and env in self.conf:
            yield self.conf.get_env(env)

        if section is None:
            # if no section specified perhaps it's an unregistered config:
            # 1. try first from core conf
            yield self.conf.core
            # 2. and then fallback to our own environment
            if current_env is not None:
                yield self.conf.get_env(current_env)
            return

        # if there's a section, special handle the core section
        if section == self.loader.core_section.name:
            yield self.conf.core  # try via registered configs
        value = self.loader.get_section(section)  # fallback to section
        if value is not None:
            yield value


@lru_cache(maxsize=None)
def _replace_ref(env: str | None) -> Pattern[str]:
    return re.compile(
        rf"""
    (\[(?P<full_env>{re.escape(env or ".*")}(:(?P<env>[^]]+))?|(?P<section>[-\w]+))])? # env/section
    (?P<key>[-a-zA-Z0-9_]+) # key
    (:(?P<default>.*))? # default value
    $
""",
        re.VERBOSE,
    )


__all__ = [
    "ReplaceReferenceIni",
]
