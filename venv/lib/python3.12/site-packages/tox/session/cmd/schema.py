"""Generate schema for tox configuration, respecting the current plugins."""

from __future__ import annotations

import json
import sys
import typing
from pathlib import Path
from typing import TYPE_CHECKING

import packaging.requirements
import packaging.version

import tox.config.set_env
import tox.config.types
import tox.tox_env.python.pip.req_file
from tox.plugin import impl

if TYPE_CHECKING:
    from tox.config.cli.parser import ToxParser
    from tox.config.sets import ConfigSet
    from tox.session.state import State


@impl
def tox_add_option(parser: ToxParser) -> None:
    our = parser.add_command("schema", [], "Generate schema for tox configuration", gen_schema)
    our.add_argument("--strict", action="store_true", help="Disallow extra properties in configuration")


def _process_type(of_type: typing.Any) -> dict[str, typing.Any]:  # noqa: C901, PLR0911
    if of_type in {
        Path,
        str,
        packaging.version.Version,
        packaging.requirements.Requirement,
        tox.tox_env.python.pip.req_file.PythonDeps,
    }:
        return {"type": "string"}
    if typing.get_origin(of_type) is typing.Union:
        types = [x for x in typing.get_args(of_type) if x is not type(None)]
        if len(types) == 1:
            return _process_type(types[0])
        msg = f"Union types are not supported: {of_type}"
        raise ValueError(msg)
    if of_type is bool:
        return {"type": "boolean"}
    if of_type is float:
        return {"type": "number"}
    if typing.get_origin(of_type) is typing.Literal:
        return {"enum": list(typing.get_args(of_type))}
    if of_type in {tox.config.types.Command, tox.config.types.EnvList}:
        return {"type": "array", "items": {"$ref": "#/definitions/subs"}}
    if typing.get_origin(of_type) in {list, set}:
        if typing.get_args(of_type)[0] in {str, packaging.requirements.Requirement}:
            return {"type": "array", "items": {"$ref": "#/definitions/subs"}}
        if typing.get_args(of_type)[0] is tox.config.types.Command:
            return {"type": "array", "items": _process_type(typing.get_args(of_type)[0])}
        msg = f"Unknown list type: {of_type}"
        raise ValueError(msg)
    if of_type is tox.config.set_env.SetEnv:
        return {
            "type": "object",
            "additionalProperties": {"$ref": "#/definitions/subs"},
        }
    if typing.get_origin(of_type) is dict:
        return {
            "type": "object",
            "additionalProperties": {**_process_type(typing.get_args(of_type)[1])},
        }
    msg = f"Unknown type: {of_type}"
    raise ValueError(msg)


def _get_schema(conf: ConfigSet, path: str) -> dict[str, dict[str, typing.Any]]:
    properties = {}
    for x in conf.get_configs():
        name, *aliases = x.keys
        of_type = getattr(x, "of_type", None)
        if of_type is None:
            continue
        desc = getattr(x, "desc", None)
        try:
            properties[name] = {**_process_type(of_type), "description": desc}
        except ValueError:
            print(name, "has unrecoginsed type:", of_type, file=sys.stderr)  # noqa: T201
        for alias in aliases:
            properties[alias] = {"$ref": f"{path}/{name}"}
    return properties


def gen_schema(state: State) -> int:
    core = state.conf.core
    strict = state.conf.options.strict

    # Accessing this adds extra stuff to core, so we need to do it first
    env_properties = _get_schema(state.envs["py"].conf, path="#/properties/env_run_base/properties")

    properties = _get_schema(core, path="#/properties")

    # This accesses plugins that register new sections (like tox-gh)
    # Accessing a private member since this is not exposed yet and the
    # interface includes the internal storage tuple
    sections = {
        key: conf
        for s, conf in state.conf._key_to_conf_set.items()  # noqa: SLF001
        if (key := s[0].split(".")[0]) not in {"env_run_base", "env_pkg_base", "env"}
    }
    for key, conf in sections.items():
        properties[key] = {
            "type": "object",
            "additionalProperties": not strict,
            "properties": _get_schema(conf, path=f"#/properties/{key}/properties"),
        }

    json_schema = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "https://github.com/tox-dev/tox/blob/main/src/tox/util/tox.schema.json",
        "type": "object",
        "properties": {
            **properties,
            "env_run_base": {
                "type": "object",
                "properties": env_properties,
                "additionalProperties": not strict,
            },
            "env_pkg_base": {
                "$ref": "#/properties/env_run_base",
                "additionalProperties": not strict,
            },
            "env": {"type": "object", "patternProperties": {"^.*$": {"$ref": "#/properties/env_run_base"}}},
            "legacy_tox_ini": {"type": "string"},
        },
        "additionalProperties": not strict,
        "definitions": {
            "subs": {
                "anyOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "properties": {
                            "replace": {"type": "string"},
                            "name": {"type": "string"},
                            "default": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"$ref": "#/definitions/subs"}},
                                ]
                            },
                            "extend": {"type": "boolean"},
                        },
                        "required": ["replace"],
                        "additionalProperties": False,
                    },
                    {
                        "type": "object",
                        "properties": {
                            "replace": {"type": "string"},
                            "of": {"type": "array", "items": {"type": "string"}},
                            "default": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"$ref": "#/definitions/subs"}},
                                ]
                            },
                            "extend": {"type": "boolean"},
                        },
                        "required": ["replace", "of"],
                        "additionalProperties": False,
                    },
                ],
            },
        },
    }
    print(json.dumps(json_schema, indent=2))  # noqa: T201
    return 0
