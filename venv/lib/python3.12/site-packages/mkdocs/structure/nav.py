from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterator, TypeVar
from urllib.parse import urlsplit

from mkdocs.exceptions import BuildError
from mkdocs.structure import StructureItem
from mkdocs.structure.files import file_sort_key
from mkdocs.structure.pages import Page, _AbsoluteLinksValidationValue
from mkdocs.utils import nest_paths

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files


log = logging.getLogger(__name__)


class Navigation:
    def __init__(self, items: list, pages: list[Page]) -> None:
        self.items = items  # Nested List with full navigation of Sections, Pages, and Links.
        self.pages = pages  # Flat List of subset of Pages in nav, in order.

        self.homepage = None
        for page in pages:
            if page.is_homepage:
                self.homepage = page
                break

    homepage: Page | None
    """The [page][mkdocs.structure.pages.Page] object for the homepage of the site."""

    pages: list[Page]
    """A flat list of all [page][mkdocs.structure.pages.Page] objects contained in the navigation."""

    def __str__(self) -> str:
        return '\n'.join(item._indent_print() for item in self)

    def __iter__(self) -> Iterator:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


class Section(StructureItem):
    def __init__(self, title: str, children: list[StructureItem]) -> None:
        self.title = title
        self.children = children

        self.active = False

    def __repr__(self):
        name = self.__class__.__name__
        return f"{name}(title={self.title!r})"

    title: str
    """The title of the section."""

    children: list[StructureItem]
    """An iterable of all child navigation objects. Children may include nested sections, pages and links."""

    @property
    def active(self) -> bool:
        """
        When `True`, indicates that a child page of this section is the current page and
        can be used to highlight the section as the currently viewed section. Defaults
        to `False`.
        """
        return self.__active

    @active.setter
    def active(self, value: bool):
        """Set active status of section and ancestors."""
        self.__active = bool(value)
        if self.parent is not None:
            self.parent.active = bool(value)

    is_section: bool = True
    """Indicates that the navigation object is a "section" object. Always `True` for section objects."""

    is_page: bool = False
    """Indicates that the navigation object is a "page" object. Always `False` for section objects."""

    is_link: bool = False
    """Indicates that the navigation object is a "link" object. Always `False` for section objects."""

    def _indent_print(self, depth: int = 0) -> str:
        ret = [super()._indent_print(depth)]
        for item in self.children:
            ret.append(item._indent_print(depth + 1))
        return '\n'.join(ret)


class Link(StructureItem):
    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url

    def __repr__(self):
        name = self.__class__.__name__
        title = f"{self.title!r}" if self.title is not None else '[blank]'
        return f"{name}(title={title}, url={self.url!r})"

    title: str
    """The title of the link. This would generally be used as the label of the link."""

    url: str
    """The URL that the link points to. The URL should always be an absolute URLs and
    should not need to have `base_url` prepended."""

    children: None = None
    """Links do not contain children and the attribute is always `None`."""

    active: bool = False
    """External links cannot be "active" and the attribute is always `False`."""

    is_section: bool = False
    """Indicates that the navigation object is a "section" object. Always `False` for link objects."""

    is_page: bool = False
    """Indicates that the navigation object is a "page" object. Always `False` for link objects."""

    is_link: bool = True
    """Indicates that the navigation object is a "link" object. Always `True` for link objects."""


def get_navigation(files: Files, config: MkDocsConfig) -> Navigation:
    """Build site navigation from config and files."""
    documentation_pages = files.documentation_pages()
    nav_config = config['nav']
    if nav_config is None:
        documentation_pages = sorted(documentation_pages, key=file_sort_key)
        nav_config = nest_paths(f.src_uri for f in documentation_pages if f.inclusion.is_in_nav())
    items = _data_to_navigation(nav_config, files, config)
    if not isinstance(items, list):
        items = [items]

    # Get only the pages from the navigation, ignoring any sections and links.
    pages = _get_by_type(items, Page)

    # Include next, previous and parent links.
    _add_previous_and_next_links(pages)
    _add_parent_links(items)

    missing_from_config = []
    for file in documentation_pages:
        if file.page is None:
            # Any documentation files not found in the nav should still have an associated page, so we
            # create them here. The Page object will automatically be assigned to `file.page` during
            # its creation (and this is the only way in which these page objects are accessible).
            Page(None, file, config)
            if file.inclusion.is_in_nav():
                missing_from_config.append(file.src_path)
    if missing_from_config:
        log.log(
            config.validation.nav.omitted_files,
            'The following pages exist in the docs directory, but are not '
            'included in the "nav" configuration:\n  - ' + '\n  - '.join(missing_from_config),
        )

    links = _get_by_type(items, Link)
    for link in links:
        scheme, netloc, path, query, fragment = urlsplit(link.url)
        if scheme or netloc:
            log.debug(f"An external link to '{link.url}' is included in the 'nav' configuration.")
        elif (
            link.url.startswith('/')
            and config.validation.nav.absolute_links
            is not _AbsoluteLinksValidationValue.RELATIVE_TO_DOCS
        ):
            log.log(
                config.validation.nav.absolute_links,
                f"An absolute path to '{link.url}' is included in the 'nav' "
                "configuration, which presumably points to an external resource.",
            )
        else:
            log.log(
                config.validation.nav.not_found,
                f"A reference to '{link.url}' is included in the 'nav' "
                "configuration, which is not found in the documentation files.",
            )
    return Navigation(items, pages)


def _data_to_navigation(data, files: Files, config: MkDocsConfig):
    if isinstance(data, dict):
        return [
            _data_to_navigation((key, value), files, config)
            if isinstance(value, str)
            else Section(title=key, children=_data_to_navigation(value, files, config))
            for key, value in data.items()
        ]
    elif isinstance(data, list):
        return [
            _data_to_navigation(item, files, config)[0]
            if isinstance(item, dict) and len(item) == 1
            else _data_to_navigation(item, files, config)
            for item in data
        ]
    title, path = data if isinstance(data, tuple) else (None, data)
    lookup_path = path
    if (
        lookup_path.startswith('/')
        and config.validation.nav.absolute_links is _AbsoluteLinksValidationValue.RELATIVE_TO_DOCS
    ):
        lookup_path = lookup_path.lstrip('/')
    if file := files.get_file_from_path(lookup_path):
        if file.inclusion.is_excluded():
            log.log(
                min(logging.INFO, config.validation.nav.not_found),
                f"A reference to '{file.src_path}' is included in the 'nav' "
                "configuration, but this file is excluded from the built site.",
            )
        page = file.page
        if page is not None:
            if not isinstance(page, Page):
                raise BuildError("A plugin has set File.page to a type other than Page.")
            return page
        return Page(title, file, config)
    return Link(title, path)


T = TypeVar('T')


def _get_by_type(nav, t: type[T]) -> list[T]:
    ret = []
    for item in nav:
        if isinstance(item, t):
            ret.append(item)
        if item.children:
            ret.extend(_get_by_type(item.children, t))
    return ret


def _add_parent_links(nav) -> None:
    for item in nav:
        if item.is_section:
            for child in item.children:
                child.parent = item
            _add_parent_links(item.children)


def _add_previous_and_next_links(pages: list[Page]) -> None:
    bookended = [None, *pages, None]
    zipped = zip(bookended[:-2], pages, bookended[2:])
    for page0, page1, page2 in zipped:
        page1.previous_page, page1.next_page = page0, page2
