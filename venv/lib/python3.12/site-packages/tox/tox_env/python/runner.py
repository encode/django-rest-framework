"""A tox run environment that handles the Python language."""

from __future__ import annotations

from abc import ABC
from functools import partial
from typing import TYPE_CHECKING, Set

from packaging.utils import canonicalize_name

from tox.config.loader.str_convert import StrConvert
from tox.report import HandledError
from tox.tox_env.errors import Skip
from tox.tox_env.python.pip.req_file import PythonDeps
from tox.tox_env.runner import RunToxEnv

from .api import Python
from .dependency_groups import resolve

if TYPE_CHECKING:
    from pathlib import Path

    from tox.config.cli.parser import Parsed
    from tox.config.sets import CoreConfigSet, EnvConfigSet
    from tox.tox_env.api import ToxEnvCreateArgs
    from tox.tox_env.package import Package


class PythonRun(Python, RunToxEnv, ABC):
    def __init__(self, create_args: ToxEnvCreateArgs) -> None:
        super().__init__(create_args)

    def register_config(self) -> None:
        super().register_config()
        root = self.core["toxinidir"]
        self.conf.add_config(
            keys="deps",
            of_type=PythonDeps,
            factory=partial(PythonDeps.factory, root),
            default=PythonDeps("", root),
            desc="Name of the python dependencies as specified by PEP-440",
        )
        self.conf.add_config(
            keys=["dependency_groups"],
            of_type=Set[str],
            default=set(),
            desc="dependency groups to install of the target package",
            post_process=_normalize_extras,
        )
        add_skip_missing_interpreters_to_core(self.core, self.options)

    @property
    def _package_types(self) -> tuple[str, ...]:
        return "wheel", "sdist", "editable", "editable-legacy", "skip", "external"

    def _register_package_conf(self) -> bool:
        # provision package type
        desc = f"package installation mode - {' | '.join(i for i in self._package_types)} "
        if not super()._register_package_conf():
            self.conf.add_constant(["package"], desc, "skip")
            return False
        if getattr(self.options, "install_pkg", None) is not None:
            self.conf.add_constant(["package"], desc, "external")
        else:
            self.conf.add_config(
                keys=["use_develop", "usedevelop"],
                desc="use develop mode",
                default=False,
                of_type=bool,
            )
            develop_mode = self.conf["use_develop"] or getattr(self.options, "develop", False)
            if develop_mode:
                self.conf.add_constant(["package"], desc, "editable")
            else:
                self.conf.add_config(keys="package", of_type=str, default=self.default_pkg_type, desc=desc)

        pkg_type = self.pkg_type
        if pkg_type == "skip":
            return False

        add_extras_to_env(self.conf)
        return True

    @property
    def default_pkg_type(self) -> str:
        return "sdist"

    @property
    def pkg_type(self) -> str:
        pkg_type: str = self.conf["package"]
        if pkg_type not in self._package_types:
            values = ", ".join(self._package_types)
            msg = f"invalid package config type {pkg_type} requested, must be one of {values}"
            raise HandledError(msg)
        return pkg_type

    def _setup_env(self) -> None:
        super()._setup_env()
        self._install_deps()
        self._install_dependency_groups()

    def _install_deps(self) -> None:
        requirements_file: PythonDeps = self.conf["deps"]
        self._install(requirements_file, PythonRun.__name__, "deps")

    def _install_dependency_groups(self) -> None:
        groups: set[str] = self.conf["dependency_groups"]
        if not groups:
            return
        try:
            root: Path = self.core["package_root"]
        except KeyError:
            root = self.core["tox_root"]
        requirements = resolve(root, groups)
        self._install(list(requirements), PythonRun.__name__, "dependency-groups")

    def _build_packages(self) -> list[Package]:
        package_env = self.package_env
        assert package_env is not None  # noqa: S101
        with package_env.display_context(self._has_display_suspended):
            try:
                packages = package_env.perform_packaging(self.conf)
            except Skip as exception:
                msg = f"{exception.args[0]} for package environment {package_env.conf['env_name']}"
                raise Skip(msg) from exception
        return packages


def add_skip_missing_interpreters_to_core(core: CoreConfigSet, options: Parsed) -> None:
    def skip_missing_interpreters_post_process(value: bool) -> bool:  # noqa: FBT001
        if getattr(options, "skip_missing_interpreters", "config") != "config":
            return StrConvert().to_bool(options.skip_missing_interpreters)
        return value

    core.add_config(
        keys=["skip_missing_interpreters"],
        default=True,
        of_type=bool,
        post_process=skip_missing_interpreters_post_process,
        desc="skip running missing interpreters",
    )


def add_extras_to_env(conf: EnvConfigSet) -> None:
    conf.add_config(
        keys=["extras"],
        of_type=Set[str],
        default=set(),
        desc="extras to install of the target package",
        post_process=_normalize_extras,
    )


def _normalize_extras(values: set[str]) -> set[str]:
    # although _ and . is allowed this will be normalized during packaging to -
    # https://packaging.python.org/en/latest/specifications/dependency-specifiers/#grammar
    return {canonicalize_name(v) for v in values}


__all__ = [
    "PythonRun",
    "add_extras_to_env",
    "add_skip_missing_interpreters_to_core",
]
