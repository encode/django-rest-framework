from __future__ import annotations

import logging
from typing import IO, Dict, Mapping

from mkdocs.config import base
from mkdocs.config import config_options as c
from mkdocs.structure.pages import Page, _AbsoluteLinksValidationValue
from mkdocs.utils.yaml import get_yaml_loader, yaml_load


class _LogLevel(c.OptionallyRequired[int]):
    levels: Mapping[str, int] = {
        "warn": logging.WARNING,
        "info": logging.INFO,
        "ignore": logging.DEBUG,
    }

    def run_validation(self, value: object) -> int:
        if not isinstance(value, str):
            raise base.ValidationError(f"Expected a string, but a {type(value)} was given.")
        try:
            return self.levels[value]
        except KeyError:
            raise base.ValidationError(f"Expected one of {list(self.levels)}, got {value!r}")


class _AbsoluteLinksValidation(_LogLevel):
    levels: Mapping[str, int] = {
        **_LogLevel.levels,
        "relative_to_docs": _AbsoluteLinksValidationValue.RELATIVE_TO_DOCS,
    }


# NOTE: The order here is important. During validation some config options
# depend on others. So, if config option A depends on B, then A should be
# listed higher in the schema.
class MkDocsConfig(base.Config):
    """The configuration of MkDocs itself (the root object of mkdocs.yml)."""

    config_file_path: str = c.Type(str)  # type: ignore[assignment]
    """The path to the mkdocs.yml config file. Can't be populated from the config."""

    site_name = c.Type(str)
    """The title to use for the documentation."""

    nav = c.Optional(c.Nav())
    """Defines the structure of the navigation."""
    pages = c.Deprecated(removed=True, moved_to='nav')

    exclude_docs = c.Optional(c.PathSpec())
    """Gitignore-like patterns of files (relative to docs dir) to exclude from the site."""

    draft_docs = c.Optional(c.PathSpec())
    """Gitignore-like patterns of files (relative to docs dir) to mark as draft."""

    not_in_nav = c.Optional(c.PathSpec())
    """Gitignore-like patterns of files (relative to docs dir) that are not intended to be in the nav.

    This marks doc files that are expected not to be in the nav, otherwise they will cause a log message
    (see also `validation.nav.omitted_files`).
    """

    site_url = c.Optional(c.URL(is_dir=True))
    """The full URL to where the documentation will be hosted."""

    site_description = c.Optional(c.Type(str))
    """A description for the documentation project that will be added to the
    HTML meta tags."""
    site_author = c.Optional(c.Type(str))
    """The name of the author to add to the HTML meta tags."""

    theme = c.Theme(default='mkdocs')
    """The MkDocs theme for the documentation."""

    docs_dir = c.DocsDir(default='docs', exists=True)
    """The directory containing the documentation markdown."""

    site_dir = c.SiteDir(default='site')
    """The directory where the site will be built to"""

    copyright = c.Optional(c.Type(str))
    """A copyright notice to add to the footer of documentation."""

    google_analytics = c.Deprecated(
        message=(
            'The configuration option {} has been deprecated and '
            'will be removed in a future release of MkDocs. See the '
            'options available on your theme for an alternative.'
        ),
        option_type=c.Type(list, length=2),
    )
    """set of values for Google analytics containing the account IO and domain
    this should look like, ['UA-27795084-5', 'mkdocs.org']"""

    dev_addr = c.IpAddress(default='127.0.0.1:8000')
    """The address on which to serve the live reloading docs server."""

    use_directory_urls = c.Type(bool, default=True)
    """If `True`, use `<page_name>/index.html` style files with hyperlinks to
    the directory. If `False`, use `<page_name>.html style file with
    hyperlinks to the file.
    True generates nicer URLs, but False is useful if browsing the output on
    a filesystem."""

    repo_url = c.Optional(c.URL())
    """Specify a link to the project source repo to be included
    in the documentation pages."""

    repo_name = c.Optional(c.RepoName('repo_url'))
    """A name to use for the link to the project source repo.
    Default, If repo_url is unset then None, otherwise
    "GitHub", "Bitbucket" or "GitLab" for known url or Hostname
    for unknown urls."""

    edit_uri_template = c.Optional(c.EditURITemplate('edit_uri'))
    edit_uri = c.Optional(c.EditURI('repo_url'))
    """Specify a URI to the docs dir in the project source repo, relative to the
    repo_url. When set, a link directly to the page in the source repo will
    be added to the generated HTML. If repo_url is not set also, this option
    is ignored."""

    extra_css = c.Type(list, default=[])
    extra_javascript = c.ListOfItems(c.ExtraScript(), default=[])
    """Specify which css or javascript files from the docs directory should be
    additionally included in the site."""

    extra_templates = c.Type(list, default=[])
    """Similar to the above, but each template (HTML or XML) will be build with
    Jinja2 and the global context."""

    markdown_extensions = c.MarkdownExtensions(
        builtins=['toc', 'tables', 'fenced_code'], configkey='mdx_configs'
    )
    """PyMarkdown extension names."""

    mdx_configs = c.Private[Dict[str, dict]]()
    """PyMarkdown extension configs. Populated from `markdown_extensions`."""

    strict = c.Type(bool, default=False)
    """Enabling strict mode causes MkDocs to stop the build when a problem is
    encountered rather than display an error."""

    remote_branch = c.Type(str, default='gh-pages')
    """The remote branch to commit to when using gh-deploy."""

    remote_name = c.Type(str, default='origin')
    """The remote name to push to when using gh-deploy."""

    extra = c.SubConfig()
    """extra is a mapping/dictionary of data that is passed to the template.
    This allows template authors to require extra configuration that not
    relevant to all themes and doesn't need to be explicitly supported by
    MkDocs itself. A good example here would be including the current
    project version."""

    plugins = c.Plugins(theme_key='theme', default=['search'])
    """A list of plugins. Each item may contain a string name or a key value pair.
    A key value pair should be the string name (as the key) and a dict of config
    options (as the value)."""

    hooks = c.Hooks('plugins')
    """A list of filenames that will be imported as Python modules and used as
    an instance of a plugin each."""

    watch = c.ListOfPaths(default=[])
    """A list of extra paths to watch while running `mkdocs serve`."""

    class Validation(base.Config):
        class NavValidation(base.Config):
            omitted_files = _LogLevel(default='info')
            """Warning level for when a doc file is never mentioned in the navigation.
            For granular configuration, see `not_in_nav`."""

            not_found = _LogLevel(default='warn')
            """Warning level for when the navigation links to a relative path that isn't an existing page on the site."""

            absolute_links = _AbsoluteLinksValidation(default='info')
            """Warning level for when the navigation links to an absolute path (starting with `/`)."""

        nav = c.SubConfig(NavValidation)

        class LinksValidation(base.Config):
            not_found = _LogLevel(default='warn')
            """Warning level for when a Markdown doc links to a relative path that isn't an existing document on the site."""

            absolute_links = _AbsoluteLinksValidation(default='info')
            """Warning level for when a Markdown doc links to an absolute path (starting with `/`)."""

            unrecognized_links = _LogLevel(default='info')
            """Warning level for when a Markdown doc links to a relative path that doesn't look like
            it could be a valid internal link. For example, if the link ends with `/`."""

            anchors = _LogLevel(default='info')
            """Warning level for when a Markdown doc links to an anchor that's not present on the target page."""

        links = c.SubConfig(LinksValidation)

    validation = c.PropagatingSubConfig[Validation]()

    _current_page: Page | None = None
    """The currently rendered page. Please do not access this and instead
    rely on the `page` argument to event handlers."""

    def load_dict(self, patch: dict) -> None:
        super().load_dict(patch)
        if 'config_file_path' in patch:
            raise base.ValidationError("Can't set config_file_path in config")

    def load_file(self, config_file: IO) -> None:
        """Load config options from the open file descriptor of a YAML file."""
        loader = get_yaml_loader(config=self)
        self.load_dict(yaml_load(config_file, loader))


def get_schema() -> base.PlainConfigSchema:
    """Soft-deprecated, do not use."""
    return MkDocsConfig._schema
