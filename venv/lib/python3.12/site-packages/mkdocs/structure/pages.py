from __future__ import annotations

import enum
import logging
import posixpath
import warnings
from typing import TYPE_CHECKING, Any, Callable, Iterator, MutableMapping, Sequence
from urllib.parse import unquote as urlunquote
from urllib.parse import urljoin, urlsplit, urlunsplit

import markdown
import markdown.extensions.toc
import markdown.htmlparser  # type: ignore
import markdown.postprocessors
import markdown.treeprocessors
from markdown.util import AMP_SUBSTITUTE

from mkdocs import utils
from mkdocs.structure import StructureItem
from mkdocs.structure.toc import get_toc
from mkdocs.utils import _removesuffix, get_build_date, get_markdown_title, meta, weak_property
from mkdocs.utils.rendering import get_heading_text

if TYPE_CHECKING:
    from xml.etree import ElementTree as etree

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File, Files
    from mkdocs.structure.toc import TableOfContents


log = logging.getLogger(__name__)


class Page(StructureItem):
    def __init__(self, title: str | None, file: File, config: MkDocsConfig) -> None:
        file.page = self
        self.file = file
        if title is not None:
            self.title = title

        # Navigation attributes
        self.children = None
        self.previous_page = None
        self.next_page = None
        self.active = False

        self.update_date: str = get_build_date()

        self._set_canonical_url(config.get('site_url', None))
        self._set_edit_url(
            config.get('repo_url', None), config.get('edit_uri'), config.get('edit_uri_template')
        )

        # Placeholders to be filled in later in the build process.
        self.markdown = None
        self._title_from_render: str | None = None
        self.content = None
        self.toc = []  # type: ignore
        self.meta = {}

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.title == other.title
            and self.file == other.file
        )

    def __repr__(self):
        name = self.__class__.__name__
        title = f"{self.title!r}" if self.title is not None else '[blank]'
        url = self.abs_url or self.file.url
        return f"{name}(title={title}, url={url!r})"

    markdown: str | None
    """The original Markdown content from the file."""

    content: str | None
    """The rendered Markdown as HTML, this is the contents of the documentation.

    Populated after `.render()`."""

    toc: TableOfContents
    """An iterable object representing the Table of contents for a page. Each item in
    the `toc` is an [`AnchorLink`][mkdocs.structure.toc.AnchorLink]."""

    meta: MutableMapping[str, Any]
    """A mapping of the metadata included at the top of the markdown page."""

    @property
    def url(self) -> str:
        """The URL of the page relative to the MkDocs `site_dir`."""
        url = self.file.url
        if url in ('.', './'):
            return ''
        return url

    file: File
    """The documentation [`File`][mkdocs.structure.files.File] that the page is being rendered from."""

    abs_url: str | None
    """The absolute URL of the page from the server root as determined by the value
    assigned to the [site_url][] configuration setting. The value includes any
    subdirectory included in the `site_url`, but not the domain. [base_url][] should
    not be used with this variable."""

    canonical_url: str | None
    """The full, canonical URL to the current page as determined by the value assigned
    to the [site_url][] configuration setting. The value includes the domain and any
    subdirectory included in the `site_url`. [base_url][] should not be used with this
    variable."""

    @property
    def active(self) -> bool:
        """When `True`, indicates that this page is the currently viewed page. Defaults to `False`."""
        return self.__active

    @active.setter
    def active(self, value: bool):
        """Set active status of page and ancestors."""
        self.__active = bool(value)
        if self.parent is not None:
            self.parent.active = bool(value)

    @property
    def is_index(self) -> bool:
        return self.file.name == 'index'

    edit_url: str | None
    """The full URL to the source page in the source repository. Typically used to
    provide a link to edit the source page. [base_url][] should not be used with this
    variable."""

    @property
    def is_homepage(self) -> bool:
        """Evaluates to `True` for the homepage of the site and `False` for all other pages."""
        return self.is_top_level and self.is_index and self.file.url in ('.', './', 'index.html')

    previous_page: Page | None
    """The [page][mkdocs.structure.pages.Page] object for the previous page or `None`.
    The value will be `None` if the current page is the first item in the site navigation
    or if the current page is not included in the navigation at all."""

    next_page: Page | None
    """The [page][mkdocs.structure.pages.Page] object for the next page or `None`.
    The value will be `None` if the current page is the last item in the site navigation
    or if the current page is not included in the navigation at all."""

    children: None = None
    """Pages do not contain children and the attribute is always `None`."""

    is_section: bool = False
    """Indicates that the navigation object is a "section" object. Always `False` for page objects."""

    is_page: bool = True
    """Indicates that the navigation object is a "page" object. Always `True` for page objects."""

    is_link: bool = False
    """Indicates that the navigation object is a "link" object. Always `False` for page objects."""

    def _set_canonical_url(self, base: str | None) -> None:
        if base:
            if not base.endswith('/'):
                base += '/'
            self.canonical_url = canonical_url = urljoin(base, self.url)
            self.abs_url = urlsplit(canonical_url).path
        else:
            self.canonical_url = None
            self.abs_url = None

    def _set_edit_url(
        self,
        repo_url: str | None,
        edit_uri: str | None = None,
        edit_uri_template: str | None = None,
    ) -> None:
        if not edit_uri_template and not edit_uri:
            self.edit_url = None
            return
        src_uri = self.file.edit_uri
        if src_uri is None:
            self.edit_url = None
            return

        if edit_uri_template:
            noext = posixpath.splitext(src_uri)[0]
            file_edit_uri = edit_uri_template.format(path=src_uri, path_noext=noext)
        else:
            assert edit_uri is not None and edit_uri.endswith('/')
            file_edit_uri = edit_uri + src_uri

        if repo_url:
            # Ensure urljoin behavior is correct
            if not file_edit_uri.startswith(('?', '#')) and not repo_url.endswith('/'):
                repo_url += '/'
        else:
            try:
                parsed_url = urlsplit(file_edit_uri)
                if not parsed_url.scheme or not parsed_url.netloc:
                    log.warning(
                        f"edit_uri: {file_edit_uri!r} is not a valid URL, it should include the http:// (scheme)"
                    )
            except ValueError as e:
                log.warning(f"edit_uri: {file_edit_uri!r} is not a valid URL: {e}")

        self.edit_url = urljoin(repo_url or '', file_edit_uri)

    def read_source(self, config: MkDocsConfig) -> None:
        source = config.plugins.on_page_read_source(page=self, config=config)
        if source is None:
            try:
                source = self.file.content_string
            except OSError:
                log.error(f'File not found: {self.file.src_path}')
                raise
            except ValueError:
                log.error(f'Encoding error reading file: {self.file.src_path}')
                raise

        self.markdown, self.meta = meta.get_data(source)

    def _set_title(self) -> None:
        warnings.warn(
            "_set_title is no longer used in MkDocs and will be removed soon.", DeprecationWarning
        )

    @weak_property
    def title(self) -> str | None:  # type: ignore[override]
        """
        Returns the title for the current page.

        Before calling `read_source()`, this value is empty. It can also be updated by `render()`.

        Checks these in order and uses the first that returns a valid title:

        - value provided on init (passed in from config)
        - value of metadata 'title'
        - content of the first H1 in Markdown content
        - convert filename to title
        """
        if self.markdown is None:
            return None

        if 'title' in self.meta:
            return self.meta['title']

        if self._title_from_render:
            return self._title_from_render
        elif self.content is None:  # Preserve legacy behavior only for edge cases in plugins.
            title_from_md = get_markdown_title(self.markdown)
            if title_from_md is not None:
                return title_from_md

        if self.is_homepage:
            return 'Home'

        title = self.file.name.replace('-', ' ').replace('_', ' ')
        # Capitalize if the filename was all lowercase, otherwise leave it as-is.
        if title.lower() == title:
            title = title.capitalize()
        return title

    def render(self, config: MkDocsConfig, files: Files) -> None:
        """Convert the Markdown source file to HTML as per the config."""
        if self.markdown is None:
            raise RuntimeError("`markdown` field hasn't been set (via `read_source`)")

        md = markdown.Markdown(
            extensions=config['markdown_extensions'],
            extension_configs=config['mdx_configs'] or {},
        )

        raw_html_ext = _RawHTMLPreprocessor()
        raw_html_ext._register(md)

        extract_anchors_ext = _ExtractAnchorsTreeprocessor(self.file, files, config)
        extract_anchors_ext._register(md)

        relative_path_ext = _RelativePathTreeprocessor(self.file, files, config)
        relative_path_ext._register(md)

        extract_title_ext = _ExtractTitleTreeprocessor()
        extract_title_ext._register(md)

        self.content = md.convert(self.markdown)
        self.toc = get_toc(getattr(md, 'toc_tokens', []))
        self._title_from_render = extract_title_ext.title
        self.present_anchor_ids = (
            extract_anchors_ext.present_anchor_ids | raw_html_ext.present_anchor_ids
        )
        if log.getEffectiveLevel() > logging.DEBUG:
            self.links_to_anchors = relative_path_ext.links_to_anchors

    present_anchor_ids: set[str] | None = None
    """Anchor IDs that this page contains (can be linked to in this page)."""

    links_to_anchors: dict[File, dict[str, str]] | None = None
    """Links to anchors in other files that this page contains.

    The structure is: `{file_that_is_linked_to: {'anchor': 'original_link/to/some_file.md#anchor'}}`.
    Populated after `.render()`. Populated only if `validation: {anchors: info}` (or greater) is set.
    """

    def validate_anchor_links(self, *, files: Files, log_level: int) -> None:
        if not self.links_to_anchors:
            return
        for to_file, links in self.links_to_anchors.items():
            for anchor, original_link in links.items():
                page = to_file.page
                if page is None:
                    continue
                if page.present_anchor_ids is None:  # Page was somehow not rendered.
                    continue
                if anchor in page.present_anchor_ids:
                    continue
                context = ""
                if to_file == self.file:
                    problem = "there is no such anchor on this page"
                    if anchor.startswith('fnref:'):
                        context = " This seems to be a footnote that is never referenced."
                else:
                    problem = f"the doc '{to_file.src_uri}' does not contain an anchor '#{anchor}'"
                log.log(
                    log_level,
                    f"Doc file '{self.file.src_uri}' contains a link '{original_link}', but {problem}.{context}",
                )


class _ExtractAnchorsTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, file: File, files: Files, config: MkDocsConfig) -> None:
        self.present_anchor_ids: set[str] = set()

    def run(self, root: etree.Element) -> None:
        add = self.present_anchor_ids.add
        for element in root.iter():
            if anchor := element.get('id'):
                add(anchor)
            if element.tag == 'a':
                if anchor := element.get('name'):
                    add(anchor)

    def _register(self, md: markdown.Markdown) -> None:
        md.treeprocessors.register(self, "mkdocs_extract_anchors", priority=5)  # Same as 'toc'.


class _RelativePathTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, file: File, files: Files, config: MkDocsConfig) -> None:
        self.file = file
        self.files = files
        self.config = config
        self.links_to_anchors: dict[File, dict[str, str]] = {}

    def run(self, root: etree.Element) -> etree.Element:
        """
        Update urls on anchors and images to make them relative.

        Iterates through the full document tree looking for specific
        tags and then makes them relative based on the site navigation
        """
        for element in root.iter():
            if element.tag == 'a':
                key = 'href'
            elif element.tag == 'img':
                key = 'src'
            else:
                continue

            url = element.get(key)
            assert url is not None
            new_url = self.path_to_url(url)
            element.set(key, new_url)

        return root

    @classmethod
    def _target_uri(cls, src_path: str, dest_path: str) -> str:
        return posixpath.normpath(
            posixpath.join(posixpath.dirname(src_path), dest_path).lstrip('/')
        )

    @classmethod
    def _possible_target_uris(
        cls, file: File, path: str, use_directory_urls: bool, suggest_absolute: bool = False
    ) -> Iterator[str]:
        """First yields the resolved file uri for the link, then proceeds to yield guesses for possible mistakes."""
        target_uri = cls._target_uri(file.src_uri, path)
        yield target_uri

        if posixpath.normpath(path) == '.':
            # Explicitly link to current file.
            yield file.src_uri
            return
        tried = {target_uri}

        prefixes = [target_uri, cls._target_uri(file.url, path)]
        if prefixes[0] == prefixes[1]:
            prefixes.pop()

        suffixes: list[Callable[[str], str]] = []
        if use_directory_urls:
            suffixes.append(lambda p: p)
        if not posixpath.splitext(target_uri)[-1]:
            suffixes.append(lambda p: posixpath.join(p, 'index.md'))
            suffixes.append(lambda p: posixpath.join(p, 'README.md'))
        if (
            not target_uri.endswith('.')
            and not path.endswith('.md')
            and (use_directory_urls or not path.endswith('/'))
        ):
            suffixes.append(lambda p: _removesuffix(p, '.html') + '.md')

        for pref in prefixes:
            for suf in suffixes:
                guess = posixpath.normpath(suf(pref))
                if guess not in tried and not guess.startswith('../'):
                    yield guess
                    tried.add(guess)

    def path_to_url(self, url: str) -> str:
        scheme, netloc, path, query, anchor = urlsplit(url)

        absolute_link = None
        warning_level, warning = 0, ''

        # Ignore URLs unless they are a relative link to a source file.
        if scheme or netloc:  # External link.
            return url
        elif url.startswith(('/', '\\')):  # Absolute link.
            absolute_link = self.config.validation.links.absolute_links
            if absolute_link is not _AbsoluteLinksValidationValue.RELATIVE_TO_DOCS:
                warning_level = absolute_link
                warning = f"Doc file '{self.file.src_uri}' contains an absolute link '{url}', it was left as is."
        elif AMP_SUBSTITUTE in url:  # AMP_SUBSTITUTE is used internally by Markdown only for email.
            return url
        elif not path:  # Self-link containing only query or anchor.
            if anchor:
                # Register that the page links to itself with an anchor.
                self.links_to_anchors.setdefault(self.file, {}).setdefault(anchor, url)
            return url

        path = urlunquote(path)
        # Determine the filepath of the target.
        possible_target_uris = self._possible_target_uris(
            self.file, path, self.config.use_directory_urls
        )

        if warning:
            # For absolute path (already has a warning), the primary lookup path should be preserved as a tip option.
            target_uri = url
            target_file = None
        else:
            # Validate that the target exists in files collection.
            target_uri = next(possible_target_uris)
            target_file = self.files.get_file_from_path(target_uri)

        if target_file is None and not warning:
            # Primary lookup path had no match, definitely produce a warning, just choose which one.
            if not posixpath.splitext(path)[-1] and absolute_link is None:
                # No '.' in the last part of a path indicates path does not point to a file.
                warning_level = self.config.validation.links.unrecognized_links
                warning = (
                    f"Doc file '{self.file.src_uri}' contains an unrecognized relative link '{url}', "
                    f"it was left as is."
                )
            else:
                target = f" '{target_uri}'" if target_uri != url.lstrip('/') else ""
                warning_level = self.config.validation.links.not_found
                warning = (
                    f"Doc file '{self.file.src_uri}' contains a link '{url}', "
                    f"but the target{target} is not found among documentation files."
                )

        if warning:
            if self.file.inclusion.is_excluded():
                warning_level = min(logging.INFO, warning_level)

            # There was no match, so try to guess what other file could've been intended.
            if warning_level > logging.DEBUG:
                suggest_url = ''
                for path in possible_target_uris:
                    if self.files.get_file_from_path(path) is not None:
                        if anchor and path == self.file.src_uri:
                            path = ''
                        elif absolute_link is _AbsoluteLinksValidationValue.RELATIVE_TO_DOCS:
                            path = '/' + path
                        else:
                            path = utils.get_relative_url(path, self.file.src_uri)
                        suggest_url = urlunsplit(('', '', path, query, anchor))
                        break
                else:
                    if '@' in url and '.' in url and '/' not in url:
                        suggest_url = f'mailto:{url}'
                if suggest_url:
                    warning += f" Did you mean '{suggest_url}'?"
            log.log(warning_level, warning)
            return url

        assert target_uri is not None
        assert target_file is not None

        if anchor:
            # Register that this page links to the target file with an anchor.
            self.links_to_anchors.setdefault(target_file, {}).setdefault(anchor, url)

        if target_file.inclusion.is_excluded():
            if self.file.inclusion.is_excluded():
                warning_level = logging.DEBUG
            else:
                warning_level = min(logging.INFO, self.config.validation.links.not_found)
            warning = (
                f"Doc file '{self.file.src_uri}' contains a link to "
                f"'{target_uri}' which is excluded from the built site."
            )
            log.log(warning_level, warning)
        path = utils.get_relative_url(target_file.url, self.file.url)
        return urlunsplit(('', '', path, query, anchor))

    def _register(self, md: markdown.Markdown) -> None:
        md.treeprocessors.register(self, "relpath", 0)


class _RawHTMLPreprocessor(markdown.preprocessors.Preprocessor):
    def __init__(self) -> None:
        super().__init__()
        self.present_anchor_ids: set[str] = set()

    def run(self, lines: list[str]) -> list[str]:
        parser = _HTMLHandler()
        parser.feed('\n'.join(lines))
        parser.close()
        self.present_anchor_ids = parser.present_anchor_ids
        return lines

    def _register(self, md: markdown.Markdown) -> None:
        md.preprocessors.register(
            self, "mkdocs_raw_html", priority=21  # Right before 'html_block'.
        )


class _HTMLHandler(markdown.htmlparser.htmlparser.HTMLParser):  # type: ignore[name-defined]
    def __init__(self) -> None:
        super().__init__()
        self.present_anchor_ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: Sequence[tuple[str, str]]) -> None:
        for k, v in attrs:
            if k == 'id' or (k == 'name' and tag == 'a'):
                self.present_anchor_ids.add(v)
        return super().handle_starttag(tag, attrs)


class _ExtractTitleTreeprocessor(markdown.treeprocessors.Treeprocessor):
    title: str | None = None
    md: markdown.Markdown

    def run(self, root: etree.Element) -> etree.Element:
        for el in root:
            if el.tag == 'h1':
                self.title = get_heading_text(el, self.md)
            break
        return root

    def _register(self, md: markdown.Markdown) -> None:
        self.md = md
        md.treeprocessors.register(self, "mkdocs_extract_title", priority=1)  # Close to the end.


class _AbsoluteLinksValidationValue(enum.IntEnum):
    RELATIVE_TO_DOCS = -1
