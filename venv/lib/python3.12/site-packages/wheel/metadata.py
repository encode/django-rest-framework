"""
Tools for converting old- to new-style metadata.
"""
from __future__ import annotations

import os.path
import textwrap
from email.message import Message
from email.parser import Parser
from typing import Iterator

from pkg_resources import Requirement, safe_extra, split_sections


def requires_to_requires_dist(requirement: Requirement) -> str:
    """Return the version specifier for a requirement in PEP 345/566 fashion."""
    if getattr(requirement, "url", None):
        return " @ " + requirement.url

    requires_dist = []
    for op, ver in requirement.specs:
        requires_dist.append(op + ver)

    if requires_dist:
        return " (" + ",".join(sorted(requires_dist)) + ")"
    else:
        return ""


def convert_requirements(requirements: list[str]) -> Iterator[str]:
    """Yield Requires-Dist: strings for parsed requirements strings."""
    for req in requirements:
        parsed_requirement = Requirement.parse(req)
        spec = requires_to_requires_dist(parsed_requirement)
        extras = ",".join(sorted(parsed_requirement.extras))
        if extras:
            extras = f"[{extras}]"

        yield parsed_requirement.project_name + extras + spec


def generate_requirements(
    extras_require: dict[str, list[str]]
) -> Iterator[tuple[str, str]]:
    """
    Convert requirements from a setup()-style dictionary to
    ('Requires-Dist', 'requirement') and ('Provides-Extra', 'extra') tuples.

    extras_require is a dictionary of {extra: [requirements]} as passed to setup(),
    using the empty extra {'': [requirements]} to hold install_requires.
    """
    for extra, depends in extras_require.items():
        condition = ""
        extra = extra or ""
        if ":" in extra:  # setuptools extra:condition syntax
            extra, condition = extra.split(":", 1)

        extra = safe_extra(extra)
        if extra:
            yield "Provides-Extra", extra
            if condition:
                condition = "(" + condition + ") and "
            condition += "extra == '%s'" % extra

        if condition:
            condition = " ; " + condition

        for new_req in convert_requirements(depends):
            yield "Requires-Dist", new_req + condition


def pkginfo_to_metadata(egg_info_path: str, pkginfo_path: str) -> Message:
    """
    Convert .egg-info directory with PKG-INFO to the Metadata 2.1 format
    """
    with open(pkginfo_path, encoding="utf-8") as headers:
        pkg_info = Parser().parse(headers)

    pkg_info.replace_header("Metadata-Version", "2.1")
    # Those will be regenerated from `requires.txt`.
    del pkg_info["Provides-Extra"]
    del pkg_info["Requires-Dist"]
    requires_path = os.path.join(egg_info_path, "requires.txt")
    if os.path.exists(requires_path):
        with open(requires_path) as requires_file:
            requires = requires_file.read()

        parsed_requirements = sorted(split_sections(requires), key=lambda x: x[0] or "")
        for extra, reqs in parsed_requirements:
            for key, value in generate_requirements({extra: reqs}):
                if (key, value) not in pkg_info.items():
                    pkg_info[key] = value

    description = pkg_info["Description"]
    if description:
        description_lines = pkg_info["Description"].splitlines()
        dedented_description = "\n".join(
            # if the first line of long_description is blank,
            # the first line here will be indented.
            (
                description_lines[0].lstrip(),
                textwrap.dedent("\n".join(description_lines[1:])),
                "\n",
            )
        )
        pkg_info.set_payload(dedented_description)
        del pkg_info["Description"]

    return pkg_info
