from __future__ import annotations

import functools
import logging
import os
import os.path
from typing import IO, TYPE_CHECKING, Any

import mergedeep  # type: ignore
import yaml
import yaml.constructor
import yaml_env_tag  # type: ignore

from mkdocs import exceptions

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

log = logging.getLogger(__name__)


def _construct_dir_placeholder(
    config: MkDocsConfig, loader: yaml.BaseLoader, node: yaml.ScalarNode
) -> _DirPlaceholder:
    loader.construct_scalar(node)

    value: str = (node and node.value) or ''
    prefix, _, suffix = value.partition('/')
    if prefix.startswith('$'):
        if prefix == '$config_dir':
            return ConfigDirPlaceholder(config, suffix)
        elif prefix == '$docs_dir':
            return DocsDirPlaceholder(config, suffix)
        else:
            raise exceptions.ConfigurationError(
                f"Unknown prefix {prefix!r} in {node.tag} {node.value!r}"
            )
    else:
        return RelativeDirPlaceholder(config, value)


class _DirPlaceholder(os.PathLike):
    def __init__(self, config: MkDocsConfig, suffix: str = ''):
        self.config = config
        self.suffix = suffix

    def value(self) -> str:
        raise NotImplementedError

    def __fspath__(self) -> str:
        """Can be used as a path."""
        return os.path.join(self.value(), self.suffix)

    def __str__(self) -> str:
        """Can be converted to a string to obtain the current class."""
        return self.__fspath__()


class ConfigDirPlaceholder(_DirPlaceholder):
    """
    A placeholder object that gets resolved to the directory of the config file when used as a path.

    The suffix can be an additional sub-path that is always appended to this path.

    This is the implementation of the `!relative $config_dir/suffix` tag, but can also be passed programmatically.
    """

    def value(self) -> str:
        return os.path.dirname(self.config.config_file_path)


class DocsDirPlaceholder(_DirPlaceholder):
    """
    A placeholder object that gets resolved to the docs dir when used as a path.

    The suffix can be an additional sub-path that is always appended to this path.

    This is the implementation of the `!relative $docs_dir/suffix` tag, but can also be passed programmatically.
    """

    def value(self) -> str:
        return self.config.docs_dir


class RelativeDirPlaceholder(_DirPlaceholder):
    """
    A placeholder object that gets resolved to the directory of the Markdown file currently being rendered.

    This is the implementation of the `!relative` tag, but can also be passed programmatically.
    """

    def __init__(self, config: MkDocsConfig, suffix: str = ''):
        if suffix:
            raise exceptions.ConfigurationError(
                f"'!relative' tag does not expect any value; received {suffix!r}"
            )
        super().__init__(config, suffix)

    def value(self) -> str:
        current_page = self.config._current_page
        if current_page is None:
            raise exceptions.ConfigurationError(
                "The current file is not set for the '!relative' tag. "
                "It cannot be used in this context; the intended usage is within `markdown_extensions`."
            )
        return os.path.dirname(os.path.join(self.config.docs_dir, current_page.file.src_path))


def get_yaml_loader(loader=yaml.Loader, config: MkDocsConfig | None = None):
    """Wrap PyYaml's loader so we can extend it to suit our needs."""

    class Loader(loader):
        """
        Define a custom loader derived from the global loader to leave the
        global loader unaltered.
        """

    # Attach Environment Variable constructor.
    # See https://github.com/waylan/pyyaml-env-tag
    Loader.add_constructor('!ENV', yaml_env_tag.construct_env_tag)

    if config is not None:
        Loader.add_constructor('!relative', functools.partial(_construct_dir_placeholder, config))

    return Loader


def yaml_load(source: IO | str, loader: type[yaml.BaseLoader] | None = None) -> dict[str, Any]:
    """Return dict of source YAML file using loader, recursively deep merging inherited parent."""
    loader = loader or get_yaml_loader()
    try:
        result = yaml.load(source, Loader=loader)
    except yaml.YAMLError as e:
        raise exceptions.ConfigurationError(
            f"MkDocs encountered an error parsing the configuration file: {e}"
        )
    if result is None:
        return {}
    if 'INHERIT' in result and not isinstance(source, str):
        relpath = result.pop('INHERIT')
        abspath = os.path.normpath(os.path.join(os.path.dirname(source.name), relpath))
        if not os.path.exists(abspath):
            raise exceptions.ConfigurationError(
                f"Inherited config file '{relpath}' does not exist at '{abspath}'."
            )
        log.debug(f"Loading inherited configuration file: {abspath}")
        with open(abspath, 'rb') as fd:
            parent = yaml_load(fd, loader)
        result = mergedeep.merge(parent, result)
    return result
