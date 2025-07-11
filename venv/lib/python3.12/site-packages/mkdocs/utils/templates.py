from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, TypedDict

if TYPE_CHECKING:
    import datetime

from markupsafe import Markup

try:
    from jinja2 import pass_context as contextfilter  # type: ignore
except ImportError:
    from jinja2 import contextfilter  # type: ignore

from mkdocs.utils import normalize_url

if TYPE_CHECKING:
    from mkdocs.config.config_options import ExtraScriptValue
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import File
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page


class TemplateContext(TypedDict):
    nav: Navigation
    pages: Sequence[File]
    base_url: str
    extra_css: Sequence[str]  # Do not use, prefer `config.extra_css`.
    extra_javascript: Sequence[str]  # Do not use, prefer `config.extra_javascript`.
    mkdocs_version: str
    build_date_utc: datetime.datetime
    config: MkDocsConfig
    page: Page | None


@contextfilter
def url_filter(context: TemplateContext, value: str) -> str:
    """A Template filter to normalize URLs."""
    return normalize_url(str(value), page=context['page'], base=context['base_url'])


@contextfilter
def script_tag_filter(context: TemplateContext, extra_script: ExtraScriptValue) -> str:
    """Converts an ExtraScript value to an HTML <script> tag line."""
    html = '<script src="{0}"'
    if not isinstance(extra_script, str):
        if extra_script.type:
            html += ' type="{1.type}"'
        if extra_script.defer:
            html += ' defer'
        if extra_script.async_:
            html += ' async'
    html += '></script>'
    return Markup(html).format(url_filter(context, str(extra_script)), extra_script)
