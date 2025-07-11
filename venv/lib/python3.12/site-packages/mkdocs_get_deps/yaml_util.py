from __future__ import annotations

import logging
import os
import os.path
from typing import IO, Any

import mergedeep  # type: ignore
import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader  # type: ignore

log = logging.getLogger(f"mkdocs.{__name__}")


class YamlLoader(SafeLoader):
    pass


# Prevent errors from trying to access external modules which may not be installed yet.
YamlLoader.add_constructor("!ENV", lambda loader, node: None)  # type: ignore
YamlLoader.add_constructor("!relative", lambda loader, node: None)  # type: ignore
YamlLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: None
)
YamlLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/object/apply:", lambda loader, suffix, node: None
)


def yaml_load(source: IO | str) -> dict[str, Any]:
    """Return dict of source YAML file using loader, recursively deep merging inherited parent."""
    result = yaml.load(source, Loader=YamlLoader)
    if result is None:
        return {}
    if (
        "INHERIT" in result
        and not isinstance(source, str)
        and getattr(source, "name", None) is not None
    ):
        relpath = result.pop("INHERIT")
        abspath = os.path.normpath(os.path.join(os.path.dirname(source.name), relpath))
        log.debug(f"Loading inherited configuration file: {abspath}")
        with open(abspath, "rb") as f:
            parent = yaml_load(f)
        result = mergedeep.merge(parent, result)
    return result
