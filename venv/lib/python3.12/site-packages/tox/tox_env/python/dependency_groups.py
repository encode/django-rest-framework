from __future__ import annotations

import sys
from collections import defaultdict
from typing import TYPE_CHECKING, TypedDict

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from tox.tox_env.errors import Fail

if TYPE_CHECKING:
    from pathlib import Path


if sys.version_info >= (3, 11):  # pragma: no cover (py311+)
    import tomllib
else:  # pragma: no cover (py311+)
    import tomli as tomllib

_IncludeGroup = TypedDict("_IncludeGroup", {"include-group": str})


def resolve(root: Path, groups: set[str]) -> set[Requirement]:
    pyproject_file = root / "pyproject.toml"
    if not pyproject_file.exists():  # check if it's static PEP-621 metadata
        return set()
    with pyproject_file.open("rb") as file_handler:
        pyproject = tomllib.load(file_handler)
    dependency_groups_raw = pyproject["dependency-groups"]
    if not isinstance(dependency_groups_raw, dict):
        msg = f"dependency-groups is {type(dependency_groups_raw).__name__} instead of table"
        raise Fail(msg)
    original_names_lookup, dependency_groups = _normalize_group_names(dependency_groups_raw)
    result: set[Requirement] = set()
    for group in groups:
        result = result.union(_resolve_dependency_group(dependency_groups, group, original_names_lookup))
    return result


def _normalize_group_names(
    dependency_groups: dict[str, list[str] | _IncludeGroup],
) -> tuple[dict[str, str], dict[str, list[str] | _IncludeGroup]]:
    original_names = defaultdict(list)
    normalized_groups = {}

    for group_name, value in dependency_groups.items():
        normed_group_name: str = canonicalize_name(group_name)
        original_names[normed_group_name].append(group_name)
        normalized_groups[normed_group_name] = value

    errors = []
    for normed_name, names in original_names.items():
        if len(names) > 1:
            errors.append(f"{normed_name} ({', '.join(names)})")
    if errors:
        msg = f"Duplicate dependency group names: {', '.join(errors)}"
        raise ValueError(msg)

    original_names_lookup = {
        normed_name: original_names[0]
        for normed_name, original_names in original_names.items()
        if len(original_names) == 1
    }

    return original_names_lookup, normalized_groups


def _resolve_dependency_group(
    dependency_groups: dict[str, list[str] | _IncludeGroup],
    group: str,
    original_names_lookup: dict[str, str],
    past_groups: tuple[str, ...] = (),
) -> set[Requirement]:
    if group in past_groups:
        original_group = original_names_lookup.get(group, group)
        original_past_groups = tuple(original_names_lookup.get(g, g) for g in past_groups)
        msg = f"Cyclic dependency group include: {original_group!r} -> {original_past_groups!r}"
        raise Fail(msg)
    if group not in dependency_groups:
        original_group = original_names_lookup.get(group, group)
        msg = f"dependency group {original_group!r} not found"
        raise Fail(msg)
    raw_group = dependency_groups[group]
    if not isinstance(raw_group, list):
        original_group = original_names_lookup.get(group, group)
        msg = f"dependency group {original_group!r} is not a list"
        raise Fail(msg)

    result = set()
    for item in raw_group:
        if isinstance(item, str):
            # packaging.requirements.Requirement parsing ensures that this is a valid
            # PEP 508 Dependency Specifier
            # raises InvalidRequirement on failure
            try:
                result.add(Requirement(item))
            except InvalidRequirement as exc:
                msg = f"{item!r} is not valid requirement due to {exc}"
                raise Fail(msg) from exc
        elif isinstance(item, dict) and tuple(item.keys()) == ("include-group",):
            include_group = canonicalize_name(next(iter(item.values())))
            result = result.union(
                _resolve_dependency_group(
                    dependency_groups, include_group, original_names_lookup, (*past_groups, group)
                )
            )
        else:
            msg = f"invalid dependency group item: {item!r}"
            raise Fail(msg)
    return result


__all__ = [
    "resolve",
]
