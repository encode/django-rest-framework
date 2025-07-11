from __future__ import annotations

__version__ = "0.2.0"

import dataclasses
import datetime
import functools
import io
import logging
import os
import sys
import urllib.parse
from typing import IO, Any, BinaryIO, Collection, Mapping, Sequence

import yaml

from . import cache, yaml_util

log = logging.getLogger(f"mkdocs.{__name__}")


DEFAULT_PROJECTS_FILE = "https://raw.githubusercontent.com/mkdocs/catalog/main/projects.yaml"

BUILTIN_THEMES = {"mkdocs", "readthedocs"}
BUILTIN_PLUGINS = {"search"}
_BUILTIN_EXTENSIONS = "abbr admonition attr_list codehilite def_list extra fenced_code footnotes md_in_html meta nl2br sane_lists smarty tables toc wikilinks legacy_attrs legacy_em".split()
BUILTIN_EXTENSIONS = {
    *_BUILTIN_EXTENSIONS,
    *(f"markdown.extensions.{e}" for e in _BUILTIN_EXTENSIONS),
}

_NotFound = ()


def _dig(cfg, keys: str):
    """
    Receives a string such as 'foo.bar' and returns `cfg['foo']['bar']`, or `_NotFound`.

    A list of single-item dicts gets converted to a flat dict. This is intended for `plugins` config.
    """
    key, _, rest = keys.partition(".")
    try:
        cfg = cfg[key]
    except (KeyError, TypeError):
        return _NotFound
    if isinstance(cfg, list):
        orig_cfg = cfg
        cfg = {}
        for item in reversed(orig_cfg):
            if isinstance(item, dict) and len(item) == 1:
                cfg.update(item)
            elif isinstance(item, str):
                cfg[item] = {}
    if not rest:
        return cfg
    return _dig(cfg, rest)


def _strings(obj) -> Sequence[str]:
    if isinstance(obj, str):
        return (obj,)
    else:
        return tuple(obj)


@functools.lru_cache(maxsize=None)
def _entry_points(group: str) -> Mapping[str, Any]:
    if sys.version_info >= (3, 10):
        from importlib.metadata import entry_points
    else:
        from importlib_metadata import entry_points

    eps = {ep.name: ep for ep in entry_points(group=group)}
    log.debug(f"Available '{group}' entry points: {sorted(eps)}")
    return eps


@dataclasses.dataclass(frozen=True)
class _PluginKind:
    projects_key: str
    entry_points_key: str

    def __str__(self) -> str:
        return self.projects_key.rpartition("_")[-1]


def get_projects_file(path: str | None = None) -> BinaryIO:
    if path is None:
        path = DEFAULT_PROJECTS_FILE
    if urllib.parse.urlsplit(path).scheme in ("http", "https"):
        content = cache.download_and_cache_url(path, datetime.timedelta(days=1))
    else:
        with open(path, "rb") as f:
            content = f.read()
    return io.BytesIO(content)


def get_deps(
    config_file: IO | os.PathLike | str | None = None,
    projects_file: IO | None = None,
) -> Collection[str]:
    """
    Print PyPI package dependencies inferred from a mkdocs.yml file based on a reverse mapping of known projects.

    Args:
        config_file: Non-default mkdocs.yml file - content as a buffer, or path.
        projects_file: File/buffer that declares all known MkDocs-related projects.
            The file is in YAML format and contains `projects: [{mkdocs_theme:, mkdocs_plugin:, markdown_extension:}]
    """
    if config_file is None:
        if os.path.isfile("mkdocs.yml"):
            config_file = "mkdocs.yml"
        elif os.path.isfile("mkdocs.yaml"):
            config_file = "mkdocs.yaml"
        else:
            config_file = "mkdocs.yml"
    opened_config_file: IO
    if isinstance(config_file, (str, os.PathLike)):
        config_file = os.path.abspath(config_file)
        opened_config_file = open(config_file, "rb")
    else:
        opened_config_file = config_file

    log.debug(f"Loading configuration file: {config_file}")
    with opened_config_file:
        cfg = yaml_util.yaml_load(opened_config_file)
    if not isinstance(cfg, dict):
        raise ValueError(
            f"The configuration is invalid. Expected a key-value mapping but received {type(cfg)}"
        )

    packages_to_install = set()

    if all(c not in cfg for c in ("site_name", "theme", "plugins", "markdown_extensions")):
        log.warning(f"The file {config_file!r} doesn't seem to be a mkdocs.yml config file")
    else:
        if _dig(cfg, "theme.locale") not in (_NotFound, "en"):
            packages_to_install.add("mkdocs[i18n]")
        else:
            packages_to_install.add("mkdocs")

    try:
        theme = cfg["theme"]["name"]
    except (KeyError, TypeError):
        theme = cfg.get("theme")
    themes = {theme} if theme else set()

    plugins = set(_strings(_dig(cfg, "plugins")))
    extensions = set(_strings(_dig(cfg, "markdown_extensions")))

    wanted_plugins = (
        (_PluginKind("mkdocs_theme", "mkdocs.themes"), themes - BUILTIN_THEMES),
        (_PluginKind("mkdocs_plugin", "mkdocs.plugins"), plugins - BUILTIN_PLUGINS),
        (_PluginKind("markdown_extension", "markdown.extensions"), extensions - BUILTIN_EXTENSIONS),
    )
    for kind, wanted in wanted_plugins:
        log.debug(f"Wanted {kind}s: {sorted(wanted)}")

    if projects_file is None:
        projects_file = get_projects_file()
    with projects_file:
        projects = yaml.load(projects_file, Loader=yaml_util.SafeLoader)["projects"]

    for project in projects:
        for kind, wanted in wanted_plugins:
            available = _strings(project.get(kind.projects_key, ()))
            for entry_name in available:
                if (  # Also check theme-namespaced plugin names against the current theme.
                    "/" in entry_name
                    and theme is not None
                    and kind.projects_key == "mkdocs_plugin"
                    and entry_name.startswith(f"{theme}/")
                    and entry_name[len(theme) + 1 :] in wanted
                    and entry_name not in wanted
                ):
                    entry_name = entry_name[len(theme) + 1 :]
                if entry_name in wanted:
                    if "pypi_id" in project:
                        install_name = project["pypi_id"]
                    elif "github_id" in project:
                        install_name = "git+https://github.com/{github_id}".format_map(project)
                    else:
                        log.error(
                            f"Can't find how to install {kind} '{entry_name}' although it was identified as {project}"
                        )
                        continue
                    packages_to_install.add(install_name)
                    for extra_key, extra_pkgs in project.get("extra_dependencies", {}).items():
                        if _dig(cfg, extra_key) is not _NotFound:
                            packages_to_install.update(_strings(extra_pkgs))

                    wanted.remove(entry_name)

    for kind, wanted in wanted_plugins:
        for entry_name in sorted(wanted):
            dist_name = None
            ep = _entry_points(kind.entry_points_key).get(entry_name)
            if ep is not None and ep.dist is not None:
                dist_name = ep.dist.name
            warning = (
                f"{str(kind).capitalize()} '{entry_name}' is not provided by any registered project"
            )
            if ep is not None:
                warning += " but is installed locally"
                if dist_name:
                    warning += f" from '{dist_name}'"
                log.info(warning)
            else:
                log.warning(warning)

    return sorted(packages_to_install)
