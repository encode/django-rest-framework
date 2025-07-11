"""Apply value substitution (replacement) on tox strings."""

from __future__ import annotations

import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Final, Sequence, Union

from tox.config.types import CircularChainError
from tox.execute.request import shell_cmd

if TYPE_CHECKING:
    from pathlib import Path

    from tox.config.loader.api import ConfigLoadArgs
    from tox.config.main import Config
    from tox.config.set_env import SetEnv


LOGGER = logging.getLogger(__name__)

# split alongside :, unless it is preceded by a single capital letter (Windows drive letters in paths)
ARG_DELIMITER: Final[str] = ":"
REPLACE_START: Final[str] = "{"
REPLACE_END: Final[str] = "}"
BACKSLASH_ESCAPE_CHARS: Final[tuple[str, ...]] = (ARG_DELIMITER, REPLACE_START, REPLACE_END, "[", "]")
MAX_REPLACE_DEPTH: Final[int] = 100


class MatchRecursionError(ValueError):
    """Could not stabilize on replacement value."""

    @staticmethod
    def check(depth: int, value: Any) -> None:
        if depth > MAX_REPLACE_DEPTH:
            msg = f"Could not expand {value} after recursing {depth} frames"
            raise MatchRecursionError(msg)


class MatchError(Exception):
    """Couldn't find end terminator in MatchExpression."""


class ReplaceReference(ABC):
    @abstractmethod
    def __call__(self, value: str, conf_args: ConfigLoadArgs) -> str | None:
        """
        Perform a reference replacement.

        :param value: the raw value
        :param conf_args: the configuration loads argument object
        :return: the replaced value, None if it can't do it.
        """
        raise NotImplementedError


MatchArg = Sequence[Union[str, "MatchExpression"]]


def find_replace_expr(value: str) -> MatchArg:
    """Find all replaceable tokens within value."""
    return MatchExpression.parse_and_split_to_terminator(value)[0][0]


def replace(conf: Config, reference: ReplaceReference, value: str, args: ConfigLoadArgs, depth: int = 0) -> str:
    """Replace all active tokens within value according to the config."""
    MatchRecursionError.check(depth, value)
    return Replacer(conf, reference, conf_args=args, depth=depth).join(find_replace_expr(value))


class MatchExpression:  # noqa: PLW1641
    """An expression that is handled specially by the Replacer."""

    def __init__(self, expr: Sequence[MatchArg], term_pos: int | None = None) -> None:
        self.expr = expr
        self.term_pos = term_pos

    def __repr__(self) -> str:
        return f"MatchExpression(expr={self.expr!r}, term_pos={self.term_pos!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self.expr == other.expr
        return NotImplemented

    @classmethod
    def _next_replace_expression(cls, value: str) -> MatchExpression | None:
        """Process a curly brace replacement expression."""
        if value.startswith("[]"):
            # `[]` is shorthand for `{posargs}`
            return MatchExpression(expr=[["posargs"]], term_pos=1)
        if not value.startswith(REPLACE_START):
            return None
        try:
            # recursively handle inner expression
            rec_expr, term_pos = cls.parse_and_split_to_terminator(
                value[1:],
                terminator=REPLACE_END,
                split=ARG_DELIMITER,
            )
        except MatchError:
            # didn't find the expected terminator character, so treat `{` as if escaped.
            pass
        else:
            return MatchExpression(expr=rec_expr, term_pos=term_pos)
        return None

    @classmethod
    def parse_and_split_to_terminator(
        cls,
        value: str,
        terminator: str = "",
        split: str | None = None,
    ) -> tuple[Sequence[MatchArg], int]:
        """
        Tokenize `value` to up `terminator` character.

        If `split` is given, multiple arguments will be returned.

        Returns list of arguments (list of str or MatchExpression) and final character position examined in value.

        This function recursively calls itself via `_next_replace_expression`.
        """
        args = []
        last_arg: list[str | MatchExpression] = []
        pos = 0

        while pos < len(value):
            if len(value) > pos + 1 and value[pos] == "\\":
                if value[pos + 1] in BACKSLASH_ESCAPE_CHARS:
                    # backslash escapes the next character from a special set
                    last_arg.append(value[pos + 1])
                    pos += 2
                    continue
                if value[pos + 1] == "\\":
                    # backlash doesn't escape a backslash, but does prevent it from affecting the next char
                    # a subsequent `shlex` pass will eat the double backslash during command splitting.
                    last_arg.append(value[pos : pos + 2])
                    pos += 2
                    continue
            fragment = value[pos:]
            if terminator and fragment.startswith(terminator):
                pos += len(terminator)
                break
            if split and fragment.startswith(split):
                # found a new argument
                args.append(last_arg)
                last_arg = []
                pos += len(split)
                continue
            expr = cls._next_replace_expression(fragment)
            if expr is not None:
                pos += (expr.term_pos or 0) + 1
                last_arg.append(expr)
                continue
            # default case: consume the next character
            last_arg.append(value[pos])
            pos += 1
        else:  # fell out of the loop
            if terminator:
                msg = f"{terminator!r} remains unmatched in {value!r}"
                raise MatchError(msg)
        args.append(last_arg)
        return [_flatten_string_fragments(a) for a in args], pos


def _flatten_string_fragments(seq_of_str_or_other: Sequence[str | Any]) -> Sequence[str | Any]:
    """Join runs of contiguous str values in a sequence; nny non-str items in the sequence are left as-is."""
    result = []
    last_str = []
    for obj in seq_of_str_or_other:
        if isinstance(obj, str):
            last_str.append(obj)
        else:
            if last_str:
                result.append("".join(last_str))
                last_str = []
            result.append(obj)
    if last_str:
        result.append("".join(last_str))
    return result


class Replacer:
    """Recursively expand MatchExpression against the config and loader."""

    def __init__(self, conf: Config, reference: ReplaceReference, conf_args: ConfigLoadArgs, depth: int = 0) -> None:
        self.conf = conf
        self.reference = reference
        self.conf_args = conf_args
        self.depth = depth

    def __call__(self, value: MatchArg) -> Sequence[str]:
        return [self._replace_match(me) if isinstance(me, MatchExpression) else str(me) for me in value]

    def join(self, value: MatchArg) -> str:
        return "".join(self(value))

    def _replace_match(self, value: MatchExpression) -> str:
        # use a copy of conf_args so any changes from this replacement don't, affect adjacent substitutions (#2869)
        conf_args = self.conf_args.copy()
        flattened_args = [self.join(arg) for arg in value.expr]
        of_type, *args = flattened_args
        if of_type == "/":
            replace_value: str | None = os.sep
        elif not of_type and args == [""]:
            replace_value = os.pathsep
        elif of_type == "env":
            replace_value = replace_env(self.conf, args, conf_args)
        elif of_type == "tty":
            replace_value = replace_tty(args)
        elif of_type == "posargs":
            replace_value = replace_pos_args(self.conf, args, conf_args)
        else:
            arg_value = ARG_DELIMITER.join(flattened_args)
            replace_value = self.reference(arg_value, conf_args)
        if replace_value is not None:
            needs_expansion = any(isinstance(m, MatchExpression) for m in find_replace_expr(replace_value))
            if needs_expansion:
                try:
                    return replace(self.conf, self.reference, replace_value, conf_args, self.depth + 1)
                except MatchRecursionError as err:
                    LOGGER.warning(str(err))
                    return replace_value
            return replace_value
        # else: fall through -- when replacement is impossible, treat `{` as if escaped.
        #     If we can't replace, keep what was there, and continue looking for additional replaces
        #     NOTE: can't raise because the content may be a factorial expression where we don't
        #           want to enforce escaping curly braces, for example`env_list = {py39,py38}-{,dep}` should work
        return f"{REPLACE_START}%s{REPLACE_END}" % ARG_DELIMITER.join(flattened_args)


def replace_pos_args(conf: Config, args: list[str], conf_args: ConfigLoadArgs) -> str:
    pos_args = load_posargs(conf, conf_args)
    # if we use the defaults, join back remaining args else take shell cmd.
    return ARG_DELIMITER.join(args) if pos_args is None else shell_cmd(pos_args)


def load_posargs(conf: Config, conf_args: ConfigLoadArgs) -> tuple[str, ...] | None:
    to_path: Path | None = None
    if conf_args.env_name is not None:  # pragma: no branch
        env_conf = conf.get_env(conf_args.env_name)
        try:
            if env_conf["args_are_paths"]:  # pragma: no branch
                to_path = env_conf["change_dir"]
        except KeyError:
            pass
    return conf.pos_args(to_path)


def replace_env(conf: Config | None, args: list[str], conf_args: ConfigLoadArgs) -> str:
    if not args or not args[0]:
        msg = "No variable name was supplied in {env} substitution"
        raise MatchError(msg)
    key = args[0]
    new_key = f"env:{key}"

    if conf is not None and conf_args.env_name is not None:  # on core no set env support # pragma: no branch
        if new_key not in conf_args.chain:  # check if set env
            conf_args.chain.append(new_key)
            env_conf = conf.get_env(conf_args.env_name)
            try:
                set_env: SetEnv = env_conf.load("set_env", chain=conf_args.chain)
            except CircularChainError:
                if not (
                    conf_args.chain[-1].endswith(".set_env")
                    and any(i.endswith(".set_env") for i in conf_args.chain[:-1])
                ):  # pragma: no branch
                    raise
            else:
                if key in set_env:
                    return set_env.load(key, conf_args)
        elif conf_args.chain[-1] != new_key:  # if there's a chain but only self-refers than use os.environ
            circular = ", ".join(i[4:] for i in conf_args.chain[conf_args.chain.index(new_key) :])
            msg = f"circular chain between set env {circular}"
            raise MatchRecursionError(msg)

    if key in os.environ:
        return os.environ[key]

    return "" if len(args) == 1 else ARG_DELIMITER.join(args[1:])


def replace_tty(args: list[str]) -> str:
    return (args[0] if len(args) > 0 else "") if sys.stdout.isatty() else args[1] if len(args) > 1 else ""


__all__ = [
    "MatchExpression",
    "MatchRecursionError",
    "find_replace_expr",
    "load_posargs",
    "replace",
    "replace_env",
]
