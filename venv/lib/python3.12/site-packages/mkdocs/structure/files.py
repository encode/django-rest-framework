from __future__ import annotations

import enum
import fnmatch
import logging
import os
import posixpath
import shutil
import warnings
from functools import cached_property
from pathlib import PurePath, PurePosixPath
from typing import TYPE_CHECKING, Callable, Iterable, Iterator, Mapping, Sequence, overload
from urllib.parse import quote as urlquote

import pathspec
import pathspec.gitignore
import pathspec.util

from mkdocs import utils

if TYPE_CHECKING:
    import jinja2.environment

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page


log = logging.getLogger(__name__)


class InclusionLevel(enum.Enum):
    EXCLUDED = -3
    """The file is excluded and will not be processed."""
    DRAFT = -2
    """The file is excluded from the final site, but will still be populated during `mkdocs serve`."""
    NOT_IN_NAV = -1
    """The file is part of the site, but doesn't produce nav warnings."""
    UNDEFINED = 0
    """Still needs to be computed based on the config. If the config doesn't kick in, acts the same as `included`."""
    INCLUDED = 1
    """The file is part of the site. Documentation pages that are omitted from the nav will produce warnings."""

    def all(self):
        return True

    def is_included(self):
        return self.value > self.DRAFT.value

    def is_excluded(self):
        return self.value <= self.DRAFT.value

    def is_in_serve(self):
        return self.value >= self.DRAFT.value

    def is_in_nav(self):
        return self.value > self.NOT_IN_NAV.value

    def is_not_in_nav(self):
        return self.value <= self.NOT_IN_NAV.value


class Files:
    """A collection of [File][mkdocs.structure.files.File] objects."""

    def __init__(self, files: Iterable[File]) -> None:
        self._src_uris = {f.src_uri: f for f in files}

    def __iter__(self) -> Iterator[File]:
        """Iterate over the files within."""
        return iter(self._src_uris.values())

    def __len__(self) -> int:
        """The number of files within."""
        return len(self._src_uris)

    def __contains__(self, path: str) -> bool:
        """Soft-deprecated, prefer `get_file_from_path(path) is not None`."""
        return PurePath(path).as_posix() in self._src_uris

    @property
    def src_paths(self) -> dict[str, File]:
        """Soft-deprecated, prefer `src_uris`."""
        return {file.src_path: file for file in self}

    @property
    def src_uris(self) -> Mapping[str, File]:
        """
        A mapping containing every file, with the keys being their
        [`src_uri`][mkdocs.structure.files.File.src_uri].
        """
        return self._src_uris

    def get_file_from_path(self, path: str) -> File | None:
        """Return a File instance with File.src_uri equal to path."""
        return self._src_uris.get(PurePath(path).as_posix())

    def append(self, file: File) -> None:
        """Add file to the Files collection."""
        if file.src_uri in self._src_uris:
            warnings.warn(
                "To replace an existing file, call `remove` before `append`.", DeprecationWarning
            )
            del self._src_uris[file.src_uri]
        self._src_uris[file.src_uri] = file

    def remove(self, file: File) -> None:
        """Remove file from Files collection."""
        try:
            del self._src_uris[file.src_uri]
        except KeyError:
            raise ValueError(f'{file.src_uri!r} not in collection')

    def copy_static_files(
        self,
        dirty: bool = False,
        *,
        inclusion: Callable[[InclusionLevel], bool] = InclusionLevel.is_included,
    ) -> None:
        """Copy static files from source to destination."""
        for file in self:
            if not file.is_documentation_page() and inclusion(file.inclusion):
                file.copy_file(dirty)

    def documentation_pages(
        self, *, inclusion: Callable[[InclusionLevel], bool] = InclusionLevel.is_included
    ) -> Sequence[File]:
        """Return iterable of all Markdown page file objects."""
        return [file for file in self if file.is_documentation_page() and inclusion(file.inclusion)]

    def static_pages(self) -> Sequence[File]:
        """Return iterable of all static page file objects."""
        return [file for file in self if file.is_static_page()]

    def media_files(self) -> Sequence[File]:
        """Return iterable of all file objects which are not documentation or static pages."""
        return [file for file in self if file.is_media_file()]

    def javascript_files(self) -> Sequence[File]:
        """Return iterable of all javascript file objects."""
        return [file for file in self if file.is_javascript()]

    def css_files(self) -> Sequence[File]:
        """Return iterable of all CSS file objects."""
        return [file for file in self if file.is_css()]

    def add_files_from_theme(self, env: jinja2.Environment, config: MkDocsConfig) -> None:
        """Retrieve static files from Jinja environment and add to collection."""

        def filter(name):
            # '.*' filters dot files/dirs at root level whereas '*/.*' filters nested levels
            patterns = ['.*', '*/.*', '*.py', '*.pyc', '*.html', '*readme*', 'mkdocs_theme.yml']
            # Exclude translation files
            patterns.append("locales/*")
            patterns.extend(f'*{x}' for x in utils.markdown_extensions)
            patterns.extend(config.theme.static_templates)
            for pattern in patterns:
                if fnmatch.fnmatch(name.lower(), pattern):
                    return False
            return True

        for path in env.list_templates(filter_func=filter):
            # Theme files do not override docs_dir files
            if self.get_file_from_path(path) is None:
                for dir in config.theme.dirs:
                    # Find the first theme dir which contains path
                    if os.path.isfile(os.path.join(dir, path)):
                        self.append(File(path, dir, config.site_dir, config.use_directory_urls))
                        break

    @property
    def _files(self) -> Iterable[File]:
        warnings.warn("Do not access Files._files.", DeprecationWarning)
        return self

    @_files.setter
    def _files(self, value: Iterable[File]):
        warnings.warn("Do not access Files._files.", DeprecationWarning)
        self._src_uris = {f.src_uri: f for f in value}


class File:
    """
    A MkDocs File object.

    It represents how the contents of one file should be populated in the destination site.

    A file always has its `abs_dest_path` (obtained by joining `dest_dir` and `dest_path`),
    where the `dest_dir` is understood to be the *site* directory.

    `content_bytes`/`content_string` (new in MkDocs 1.6) can always be used to obtain the file's
    content. But it may be backed by one of the two sources:

    *   A physical source file at `abs_src_path` (by default obtained by joining `src_dir` and
        `src_uri`). `src_dir` is understood to be the *docs* directory.

        Then `content_bytes`/`content_string` will read the file at `abs_src_path`.

        `src_dir` *should* be populated for real files and should be `None` for generated files.

    *   Since MkDocs 1.6 a file may alternatively be stored in memory - `content_string`/`content_bytes`.

        Then `src_dir` and `abs_src_path` will remain `None`. `content_bytes`/`content_string` need
        to be written to, or populated through the `content` argument in the constructor.

        But `src_uri` is still populated for such files as well! The virtual file pretends as if it
        originated from that path in the `docs` directory, and other values are derived.

    For static files the file is just copied to the destination, and `dest_uri` equals `src_uri`.

    For Markdown files (determined by the file extension in `src_uri`) the destination content
    will be the rendered content, and `dest_uri` will have the `.html` extension and some
    additional transformations to the path, based on `use_directory_urls`.
    """

    src_uri: str
    """The pure path (always '/'-separated) of the source file relative to the source directory."""

    use_directory_urls: bool
    """Whether directory URLs ('foo/') should be used or not ('foo.html').

    If `False`, a Markdown file is mapped to an HTML file of the same name (the file extension is
    changed to `.html`). If True, a Markdown file is mapped to an HTML index file (`index.html`)
    nested in a directory using the "name" of the file in `path`. Non-Markdown files retain their
    original path.
    """

    src_dir: str | None
    """The OS path of the top-level directory that the source file originates from.

    Assumed to be the *docs_dir*; not populated for generated files."""

    dest_dir: str
    """The OS path of the destination directory (top-level site_dir) that the file should be copied to."""

    inclusion: InclusionLevel = InclusionLevel.UNDEFINED
    """Whether the file will be excluded from the built site."""

    generated_by: str | None = None
    """If not None, indicates that a plugin generated this file on the fly.

    The value is the plugin's entrypoint name and can be used to find the plugin by key in the PluginCollection."""

    _content: str | bytes | None = None
    """If set, the file's content will be read from here.

    This logic is handled by `content_bytes`/`content_string`, which should be used instead of
    accessing this attribute."""

    @property
    def src_path(self) -> str:
        """Same as `src_uri` (and synchronized with it) but will use backslashes on Windows. Discouraged."""
        return os.path.normpath(self.src_uri)

    @src_path.setter
    def src_path(self, value: str):
        self.src_uri = PurePath(value).as_posix()

    @property
    def dest_path(self) -> str:
        """Same as `dest_uri` (and synchronized with it) but will use backslashes on Windows. Discouraged."""
        return os.path.normpath(self.dest_uri)

    @dest_path.setter
    def dest_path(self, value: str):
        self.dest_uri = PurePath(value).as_posix()

    page: Page | None = None

    @overload
    @classmethod
    def generated(
        cls,
        config: MkDocsConfig,
        src_uri: str,
        *,
        content: str | bytes,
        inclusion: InclusionLevel = InclusionLevel.UNDEFINED,
    ) -> File:
        """
        Create a virtual file backed by in-memory content.

        It will pretend to be a file in the docs dir at `src_uri`.
        """

    @overload
    @classmethod
    def generated(
        cls,
        config: MkDocsConfig,
        src_uri: str,
        *,
        abs_src_path: str,
        inclusion: InclusionLevel = InclusionLevel.UNDEFINED,
    ) -> File:
        """
        Create a virtual file backed by a physical temporary file at `abs_src_path`.

        It will pretend to be a file in the docs dir at `src_uri`.
        """

    @classmethod
    def generated(
        cls,
        config: MkDocsConfig,
        src_uri: str,
        *,
        content: str | bytes | None = None,
        abs_src_path: str | None = None,
        inclusion: InclusionLevel = InclusionLevel.UNDEFINED,
    ) -> File:
        """
        Create a virtual file, backed either by in-memory `content` or by a file at `abs_src_path`.

        It will pretend to be a file in the docs dir at `src_uri`.
        """
        if (content is None) == (abs_src_path is None):
            raise TypeError("File must have exactly one of 'content' or 'abs_src_path'")
        f = cls(
            src_uri,
            src_dir=None,
            dest_dir=config.site_dir,
            use_directory_urls=config.use_directory_urls,
            inclusion=inclusion,
        )
        f.generated_by = config.plugins._current_plugin or '<unknown>'
        f.abs_src_path = abs_src_path
        f._content = content
        return f

    def __init__(
        self,
        path: str,
        src_dir: str | None,
        dest_dir: str,
        use_directory_urls: bool,
        *,
        dest_uri: str | None = None,
        inclusion: InclusionLevel = InclusionLevel.UNDEFINED,
    ) -> None:
        self.src_path = path
        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self.use_directory_urls = use_directory_urls
        if dest_uri is not None:
            self.dest_uri = dest_uri
        self.inclusion = inclusion

    def __repr__(self):
        return (
            f"{type(self).__name__}({self.src_uri!r}, src_dir={self.src_dir!r}, "
            f"dest_dir={self.dest_dir!r}, use_directory_urls={self.use_directory_urls!r}, "
            f"dest_uri={self.dest_uri!r}, inclusion={self.inclusion})"
        )

    @utils.weak_property
    def edit_uri(self) -> str | None:
        """
        A path relative to the source repository to use for the "edit" button.

        Defaults to `src_uri` and can be overwritten.
        For generated files this should be set to `None`.
        """
        return self.src_uri if self.generated_by is None else None

    def _get_stem(self) -> str:
        """Soft-deprecated, do not use."""
        filename = posixpath.basename(self.src_uri)
        stem, ext = posixpath.splitext(filename)
        return 'index' if stem == 'README' else stem

    name = cached_property(_get_stem)
    """Return the name of the file without its extension."""

    def _get_dest_path(self, use_directory_urls: bool | None = None) -> str:
        """Soft-deprecated, do not use."""
        if self.is_documentation_page():
            parent, filename = posixpath.split(self.src_uri)
            if use_directory_urls is None:
                use_directory_urls = self.use_directory_urls
            if not use_directory_urls or self.name == 'index':
                # index.md or README.md => index.html
                # foo.md => foo.html
                return posixpath.join(parent, self.name + '.html')
            else:
                # foo.md => foo/index.html
                return posixpath.join(parent, self.name, 'index.html')
        return self.src_uri

    dest_uri = cached_property(_get_dest_path)
    """The pure path (always '/'-separated) of the destination file relative to the destination directory."""

    def _get_url(self, use_directory_urls: bool | None = None) -> str:
        """Soft-deprecated, do not use."""
        url = self.dest_uri
        dirname, filename = posixpath.split(url)
        if use_directory_urls is None:
            use_directory_urls = self.use_directory_urls
        if use_directory_urls and filename == 'index.html':
            url = (dirname or '.') + '/'
        return urlquote(url)

    url = cached_property(_get_url)
    """The URI of the destination file relative to the destination directory as a string."""

    @cached_property
    def abs_src_path(self) -> str | None:
        """
        The absolute concrete path of the source file. Will use backslashes on Windows.

        Note: do not use this path to read the file, prefer `content_bytes`/`content_string`.
        """
        if self.src_dir is None:
            return None
        return os.path.normpath(os.path.join(self.src_dir, self.src_uri))

    @cached_property
    def abs_dest_path(self) -> str:
        """The absolute concrete path of the destination file. Will use backslashes on Windows."""
        return os.path.normpath(os.path.join(self.dest_dir, self.dest_uri))

    def url_relative_to(self, other: File | str) -> str:
        """Return url for file relative to other file."""
        return utils.get_relative_url(self.url, other.url if isinstance(other, File) else other)

    @property
    def content_bytes(self) -> bytes:
        """
        Get the content of this file as a bytestring.

        May raise if backed by a real file (`abs_src_path`) if it cannot be read.

        If used as a setter, it defines the content of the file, and `abs_src_path` becomes unset.
        """
        content = self._content
        if content is None:
            assert self.abs_src_path is not None
            with open(self.abs_src_path, 'rb') as f:
                return f.read()
        if not isinstance(content, bytes):
            content = content.encode()
        return content

    @content_bytes.setter
    def content_bytes(self, value: bytes):
        assert isinstance(value, bytes)
        self._content = value
        self.abs_src_path = None

    @property
    def content_string(self) -> str:
        """
        Get the content of this file as a string. Assumes UTF-8 encoding, may raise.

        May also raise if backed by a real file (`abs_src_path`) if it cannot be read.

        If used as a setter, it defines the content of the file, and `abs_src_path` becomes unset.
        """
        content = self._content
        if content is None:
            assert self.abs_src_path is not None
            with open(self.abs_src_path, encoding='utf-8-sig', errors='strict') as f:
                return f.read()
        if not isinstance(content, str):
            content = content.decode('utf-8-sig', errors='strict')
        return content

    @content_string.setter
    def content_string(self, value: str):
        assert isinstance(value, str)
        self._content = value
        self.abs_src_path = None

    def copy_file(self, dirty: bool = False) -> None:
        """Copy source file to destination, ensuring parent directories exist."""
        if dirty and not self.is_modified():
            log.debug(f"Skip copying unmodified file: '{self.src_uri}'")
            return
        log.debug(f"Copying media file: '{self.src_uri}'")
        output_path = self.abs_dest_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        content = self._content
        if content is None:
            assert self.abs_src_path is not None
            try:
                utils.copy_file(self.abs_src_path, output_path)
            except shutil.SameFileError:
                pass  # Let plugins write directly into site_dir.
        elif isinstance(content, str):
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.write(content)
        else:
            with open(output_path, 'wb') as output_file:
                output_file.write(content)

    def is_modified(self) -> bool:
        if self._content is not None:
            return True
        assert self.abs_src_path is not None
        if os.path.isfile(self.abs_dest_path):
            return os.path.getmtime(self.abs_dest_path) < os.path.getmtime(self.abs_src_path)
        return True

    def is_documentation_page(self) -> bool:
        """Return True if file is a Markdown page."""
        return utils.is_markdown_file(self.src_uri)

    def is_static_page(self) -> bool:
        """Return True if file is a static page (HTML, XML, JSON)."""
        return self.src_uri.endswith(('.html', '.htm', '.xml', '.json'))

    def is_media_file(self) -> bool:
        """Return True if file is not a documentation or static page."""
        return not (self.is_documentation_page() or self.is_static_page())

    def is_javascript(self) -> bool:
        """Return True if file is a JavaScript file."""
        return self.src_uri.endswith(('.js', '.javascript', '.mjs'))

    def is_css(self) -> bool:
        """Return True if file is a CSS file."""
        return self.src_uri.endswith('.css')


_default_exclude = pathspec.gitignore.GitIgnoreSpec.from_lines(['.*', '/templates/'])


def set_exclusions(files: Iterable[File], config: MkDocsConfig) -> None:
    """Re-calculate which files are excluded, based on the patterns in the config."""
    exclude: pathspec.gitignore.GitIgnoreSpec | None = config.get('exclude_docs')
    exclude = _default_exclude + exclude if exclude else _default_exclude
    drafts: pathspec.gitignore.GitIgnoreSpec | None = config.get('draft_docs')
    nav_exclude: pathspec.gitignore.GitIgnoreSpec | None = config.get('not_in_nav')

    for file in files:
        if file.inclusion == InclusionLevel.UNDEFINED:
            if exclude.match_file(file.src_uri):
                file.inclusion = InclusionLevel.EXCLUDED
            elif drafts and drafts.match_file(file.src_uri):
                file.inclusion = InclusionLevel.DRAFT
            elif nav_exclude and nav_exclude.match_file(file.src_uri):
                file.inclusion = InclusionLevel.NOT_IN_NAV
            else:
                file.inclusion = InclusionLevel.INCLUDED


def get_files(config: MkDocsConfig) -> Files:
    """Walk the `docs_dir` and return a Files collection."""
    files: list[File] = []
    conflicting_files: list[tuple[File, File]] = []
    for source_dir, dirnames, filenames in os.walk(config['docs_dir'], followlinks=True):
        relative_dir = os.path.relpath(source_dir, config['docs_dir'])
        dirnames.sort()
        filenames.sort(key=_file_sort_key)

        files_by_dest: dict[str, File] = {}
        for filename in filenames:
            file = File(
                os.path.join(relative_dir, filename),
                config['docs_dir'],
                config['site_dir'],
                config['use_directory_urls'],
            )
            # Skip README.md if an index file also exists in dir (part 1)
            prev_file = files_by_dest.setdefault(file.dest_uri, file)
            if prev_file is not file:
                conflicting_files.append((prev_file, file))
            files.append(file)
            prev_file = file

    set_exclusions(files, config)
    # Skip README.md if an index file also exists in dir (part 2)
    for a, b in conflicting_files:
        if b.inclusion.is_included():
            if a.inclusion.is_included():
                log.warning(
                    f"Excluding '{a.src_uri}' from the site because it conflicts with '{b.src_uri}'."
                )
            try:
                files.remove(a)
            except ValueError:
                pass  # Catching this to avoid errors if attempting to remove the same file twice.
        else:
            try:
                files.remove(b)
            except ValueError:
                pass

    return Files(files)


def file_sort_key(f: File, /):
    """
    Replicates the sort order how `get_files` produces it - index first, directories last.

    To sort a list of `File`, pass as the `key` argument to `sort`.
    """
    parts = PurePosixPath(f.src_uri).parts
    if not parts:
        return ()
    return (parts[:-1], f.name != "index", parts[-1])


def _file_sort_key(f: str):
    """Always sort `index` or `README` as first filename in list. This works only on basenames of files."""
    return (os.path.splitext(f)[0] not in ('index', 'README'), f)


def _sort_files(filenames: Iterable[str]) -> list[str]:
    """Soft-deprecated, do not use."""
    return sorted(filenames, key=_file_sort_key)


def _filter_paths(basename: str, path: str, is_dir: bool, exclude: Iterable[str]) -> bool:
    warnings.warn(
        "_filter_paths is not used since MkDocs 1.5 and will be removed soon.", DeprecationWarning
    )
    for item in exclude:
        # Items ending in '/' apply only to directories.
        if item.endswith('/') and not is_dir:
            continue
        # Items starting with '/' apply to the whole path.
        # In any other cases just the basename is used.
        match = path if item.startswith('/') else basename
        if fnmatch.fnmatch(match, item.strip('/')):
            return True
    return False
