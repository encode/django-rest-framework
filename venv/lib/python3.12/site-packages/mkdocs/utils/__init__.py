"""
Standalone file utils.

Nothing in this module should have an knowledge of config or the layout
and structure of the site and pages in the site.
"""
from __future__ import annotations

import functools
import logging
import os
import posixpath
import re
import shutil
import sys
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import PurePath
from typing import TYPE_CHECKING, Collection, Iterable, MutableSequence, TypeVar
from urllib.parse import urlsplit

if sys.version_info >= (3, 10):
    from importlib.metadata import EntryPoint, entry_points
else:
    from importlib_metadata import EntryPoint, entry_points

from mkdocs import exceptions
from mkdocs.utils.yaml import get_yaml_loader, yaml_load  # noqa: F401 - legacy re-export

if TYPE_CHECKING:
    from mkdocs.structure.pages import Page

T = TypeVar('T')

log = logging.getLogger(__name__)

markdown_extensions = (
    '.markdown',
    '.mdown',
    '.mkdn',
    '.mkd',
    '.md',
)


def get_build_timestamp(*, pages: Collection[Page] | None = None) -> int:
    """
    Returns the number of seconds since the epoch for the latest updated page.

    In reality this is just today's date because that's how pages' update time is populated.
    """
    if pages:
        # Lexicographic comparison is OK for ISO date.
        date_string = max(p.update_date for p in pages)
        dt = datetime.fromisoformat(date_string)
    else:
        dt = get_build_datetime()
    return int(dt.timestamp())


def get_build_datetime() -> datetime:
    """
    Returns an aware datetime object.

    Support SOURCE_DATE_EPOCH environment variable for reproducible builds.
    See https://reproducible-builds.org/specs/source-date-epoch/
    """
    source_date_epoch = os.environ.get('SOURCE_DATE_EPOCH')
    if source_date_epoch is None:
        return datetime.now(timezone.utc)

    return datetime.fromtimestamp(int(source_date_epoch), timezone.utc)


def get_build_date() -> str:
    """
    Returns the displayable date string.

    Support SOURCE_DATE_EPOCH environment variable for reproducible builds.
    See https://reproducible-builds.org/specs/source-date-epoch/
    """
    return get_build_datetime().strftime('%Y-%m-%d')


if sys.version_info >= (3, 9):
    _removesuffix = str.removesuffix
else:

    def _removesuffix(s: str, suffix: str) -> str:
        if suffix and s.endswith(suffix):
            return s[: -len(suffix)]
        return s


def reduce_list(data_set: Iterable[T]) -> list[T]:
    """Reduce duplicate items in a list and preserve order."""
    return list(dict.fromkeys(data_set))


if sys.version_info >= (3, 10):
    from bisect import insort
else:

    def insort(a: MutableSequence[T], x: T, *, key=lambda v: v) -> None:
        kx = key(x)
        i = len(a)
        while i > 0 and kx < key(a[i - 1]):
            i -= 1
        a.insert(i, x)


def copy_file(source_path: str, output_path: str) -> None:
    """
    Copy source_path to output_path, making sure any parent directories exist.

    The output_path may be a directory.
    """
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, os.path.basename(source_path))
    shutil.copyfile(source_path, output_path)


def write_file(content: bytes, output_path: str) -> None:
    """Write content to output_path, making sure any parent directories exist."""
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(content)


def clean_directory(directory: str) -> None:
    """Remove the content of a directory recursively but not the directory itself."""
    if not os.path.exists(directory):
        return

    for entry in os.listdir(directory):
        # Don't remove hidden files from the directory. We never copy files
        # that are hidden, so we shouldn't delete them either.
        if entry.startswith('.'):
            continue

        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            shutil.rmtree(path, True)
        else:
            os.unlink(path)


def is_markdown_file(path: str) -> bool:
    """
    Return True if the given file path is a Markdown file.

    https://superuser.com/questions/249436/file-extension-for-markdown-files
    """
    return path.endswith(markdown_extensions)


_ERROR_TEMPLATE_RE = re.compile(r'^\d{3}\.html?$')


def is_error_template(path: str) -> bool:
    """Return True if the given file path is an HTTP error template."""
    return bool(_ERROR_TEMPLATE_RE.match(path))


@functools.lru_cache(maxsize=None)
def _norm_parts(path: str) -> list[str]:
    if not path.startswith('/'):
        path = '/' + path
    path = posixpath.normpath(path)[1:]
    return path.split('/') if path else []


def get_relative_url(url: str, other: str) -> str:
    """
    Return given url relative to other.

    Both are operated as slash-separated paths, similarly to the 'path' part of a URL.
    The last component of `other` is skipped if it contains a dot (considered a file).
    Actual URLs (with schemas etc.) aren't supported. The leading slash is ignored.
    Paths are normalized ('..' works as parent directory), but going higher than the
    root has no effect ('foo/../../bar' ends up just as 'bar').
    """
    # Remove filename from other url if it has one.
    dirname, _, basename = other.rpartition('/')
    if '.' in basename:
        other = dirname

    other_parts = _norm_parts(other)
    dest_parts = _norm_parts(url)
    common = 0
    for a, b in zip(other_parts, dest_parts):
        if a != b:
            break
        common += 1

    rel_parts = ['..'] * (len(other_parts) - common) + dest_parts[common:]
    relurl = '/'.join(rel_parts) or '.'
    return relurl + '/' if url.endswith('/') else relurl


def normalize_url(path: str, page: Page | None = None, base: str = '') -> str:
    """Return a URL relative to the given page or using the base."""
    path, relative_level = _get_norm_url(path)
    if relative_level == -1:
        return path
    if page is not None:
        result = get_relative_url(path, page.url)
        if relative_level > 0:
            result = '../' * relative_level + result
        return result

    return posixpath.join(base, path)


@functools.lru_cache(maxsize=None)
def _get_norm_url(path: str) -> tuple[str, int]:
    if not path:
        path = '.'
    elif '\\' in path:
        log.warning(
            f"Path '{path}' uses OS-specific separator '\\'. "
            f"That will be unsupported in a future release. Please change it to '/'."
        )
        path = path.replace('\\', '/')
    # Allow links to be fully qualified URLs
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or path.startswith(('/', '#')):
        return path, -1

    # Relative path - preserve information about it
    norm = posixpath.normpath(path) + '/'
    relative_level = 0
    while norm.startswith('../', relative_level * 3):
        relative_level += 1
    return path, relative_level


def create_media_urls(
    path_list: Iterable[str], page: Page | None = None, base: str = ''
) -> list[str]:
    """Soft-deprecated, do not use."""
    return [normalize_url(path, page, base) for path in path_list]


def path_to_url(path):
    warnings.warn(
        "path_to_url is never used in MkDocs and will be removed soon.", DeprecationWarning
    )
    return path.replace('\\', '/')


def get_theme_dir(name: str) -> str:
    """Return the directory of an installed theme by name."""
    theme = get_themes()[name]
    return os.path.dirname(os.path.abspath(theme.load().__file__))


@functools.lru_cache(maxsize=None)
def get_themes() -> dict[str, EntryPoint]:
    """Return a dict of all installed themes as {name: EntryPoint}."""
    themes: dict[str, EntryPoint] = {}
    eps: dict[EntryPoint, None] = dict.fromkeys(entry_points(group='mkdocs.themes'))
    builtins = {ep.name for ep in eps if ep.dist is not None and ep.dist.name == 'mkdocs'}

    for theme in eps:
        assert theme.dist is not None

        if theme.name in builtins and theme.dist.name != 'mkdocs':
            raise exceptions.ConfigurationError(
                f"The theme '{theme.name}' is a builtin theme but the package '{theme.dist.name}' "
                "attempts to provide a theme with the same name."
            )
        elif theme.name in themes:
            other_dist = themes[theme.name].dist
            assert other_dist is not None
            log.warning(
                f"A theme named '{theme.name}' is provided by the Python packages '{theme.dist.name}' "
                f"and '{other_dist.name}'. The one in '{theme.dist.name}' will be used."
            )

        themes[theme.name] = theme

    return themes


def get_theme_names() -> Collection[str]:
    """Return a list of all installed themes by name."""
    return get_themes().keys()


def dirname_to_title(dirname: str) -> str:
    """Return a page tile obtained from a directory name."""
    title = dirname
    title = title.replace('-', ' ').replace('_', ' ')
    # Capitalize if the dirname was all lowercase, otherwise leave it as-is.
    if title.lower() == title:
        title = title.capitalize()

    return title


def get_markdown_title(markdown_src: str) -> str | None:
    """Soft-deprecated, do not use."""
    lines = markdown_src.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines:
        line = lines.pop(0).strip()
        if not line.strip():
            continue
        if not line.startswith('# '):
            return None
        return line.lstrip('# ')
    return None


def find_or_create_node(branch, key):
    """
    Given a list, look for dictionary with a key matching key and return it's
    value. If it doesn't exist, create it with the value of an empty list and
    return that.
    """
    for node in branch:
        if not isinstance(node, dict):
            continue

        if key in node:
            return node[key]

    new_branch = []
    node = {key: new_branch}
    branch.append(node)
    return new_branch


def nest_paths(paths):
    """
    Given a list of paths, convert them into a nested structure that will match
    the pages config.
    """
    nested = []

    for path in paths:
        parts = PurePath(path).parent.parts

        branch = nested
        for part in parts:
            part = dirname_to_title(part)
            branch = find_or_create_node(branch, part)

        branch.append(path)

    return nested


class DuplicateFilter:
    """Avoid logging duplicate messages."""

    def __init__(self) -> None:
        self.msgs: set[str] = set()

    def __call__(self, record: logging.LogRecord) -> bool:
        rv = record.msg not in self.msgs
        self.msgs.add(record.msg)
        return rv


class CountHandler(logging.NullHandler):
    """Counts all logged messages >= level."""

    def __init__(self, **kwargs) -> None:
        self.counts: dict[int, int] = defaultdict(int)
        super().__init__(**kwargs)

    def handle(self, record):
        rv = self.filter(record)
        if rv:
            # Use levelno for keys so they can be sorted later
            self.counts[record.levelno] += 1
        return rv

    def get_counts(self) -> list[tuple[str, int]]:
        return [(logging.getLevelName(k), v) for k, v in sorted(self.counts.items(), reverse=True)]


class weak_property:
    """Same as a read-only property, but allows overwriting the field for good."""

    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self.func(instance)


def __getattr__(name: str):
    if name == 'warning_filter':
        warnings.warn(
            "warning_filter doesn't do anything since MkDocs 1.2 and will be removed soon. "
            "All messages on the `mkdocs` logger get counted automatically.",
            DeprecationWarning,
        )
        return logging.Filter()

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
