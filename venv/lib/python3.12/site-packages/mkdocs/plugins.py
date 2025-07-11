"""Implements the plugin API for MkDocs."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, MutableMapping, TypeVar, overload

if sys.version_info >= (3, 10):
    from importlib.metadata import EntryPoint, entry_points
else:
    from importlib_metadata import EntryPoint, entry_points

if TYPE_CHECKING:
    import jinja2.environment

from mkdocs import utils
from mkdocs.config.base import Config, ConfigErrors, ConfigWarnings, LegacyConfig, PlainConfigSchema

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.livereload import LiveReloadServer
    from mkdocs.structure.files import Files
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page
    from mkdocs.utils.templates import TemplateContext

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec
else:
    ParamSpec = TypeVar

P = ParamSpec('P')
T = TypeVar('T')


log = logging.getLogger('mkdocs.plugins')


def get_plugins() -> dict[str, EntryPoint]:
    """Return a dict of all installed Plugins as {name: EntryPoint}."""
    plugins = entry_points(group='mkdocs.plugins')

    # Allow third-party plugins to override core plugins
    pluginmap = {}
    for plugin in plugins:
        if plugin.name in pluginmap and plugin.value.startswith("mkdocs.contrib."):
            continue

        pluginmap[plugin.name] = plugin

    return pluginmap


SomeConfig = TypeVar('SomeConfig', bound=Config)


class BasePlugin(Generic[SomeConfig]):
    """
    Plugin base class.

    All plugins should subclass this class.
    """

    config_class: type[SomeConfig] = LegacyConfig  # type: ignore[assignment]
    config_scheme: PlainConfigSchema = ()
    config: SomeConfig = {}  # type: ignore[assignment]

    supports_multiple_instances: bool = False
    """Set to true in subclasses to declare support for adding the same plugin multiple times."""

    def __class_getitem__(cls, config_class: type[Config]):
        """Eliminates the need to write `config_class = FooConfig` when subclassing BasePlugin[FooConfig]."""
        name = f'{cls.__name__}[{config_class.__name__}]'
        return type(name, (cls,), dict(config_class=config_class))

    def __init_subclass__(cls):
        if not issubclass(cls.config_class, Config):
            raise TypeError(
                f"config_class {cls.config_class} must be a subclass of `mkdocs.config.base.Config`"
            )
        if cls.config_class is not LegacyConfig:
            cls.config_scheme = cls.config_class._schema  # For compatibility.

    def load_config(
        self, options: dict[str, Any], config_file_path: str | None = None
    ) -> tuple[ConfigErrors, ConfigWarnings]:
        """Load config from a dict of options. Returns a tuple of (errors, warnings)."""
        if self.config_class is LegacyConfig:
            self.config = LegacyConfig(self.config_scheme, config_file_path=config_file_path)  # type: ignore
        else:
            self.config = self.config_class(config_file_path=config_file_path)

        self.config.load_dict(options)

        return self.config.validate()

    # One-time events

    def on_startup(self, *, command: Literal['build', 'gh-deploy', 'serve'], dirty: bool) -> None:
        """
        The `startup` event runs once at the very beginning of an `mkdocs` invocation.

        New in MkDocs 1.4.

        The presence of an `on_startup` method (even if empty) migrates the plugin to the new
        system where the plugin object is kept across builds within one `mkdocs serve`.

        Note that for initializing variables, the `__init__` method is still preferred.
        For initializing per-build variables (and whenever in doubt), use the `on_config` event.

        Args:
            command: the command that MkDocs was invoked with, e.g. "serve" for `mkdocs serve`.
            dirty: whether `--dirty` flag was passed.
        """

    def on_shutdown(self) -> None:
        """
        The `shutdown` event runs once at the very end of an `mkdocs` invocation, before exiting.

        This event is relevant only for support of `mkdocs serve`, otherwise within a
        single build it's undistinguishable from `on_post_build`.

        New in MkDocs 1.4.

        The presence of an `on_shutdown` method (even if empty) migrates the plugin to the new
        system where the plugin object is kept across builds within one `mkdocs serve`.

        Note the `on_post_build` method is still preferred for cleanups, when possible, as it has
        a much higher chance of actually triggering. `on_shutdown` is "best effort" because it
        relies on detecting a graceful shutdown of MkDocs.
        """

    def on_serve(
        self, server: LiveReloadServer, /, *, config: MkDocsConfig, builder: Callable
    ) -> LiveReloadServer | None:
        """
        The `serve` event is only called when the `serve` command is used during
        development. It runs only once, after the first build finishes.
        It is passed the `Server` instance which can be modified before
        it is activated. For example, additional files or directories could be added
        to the list of "watched" files for auto-reloading.

        Args:
            server: `livereload.Server` instance
            config: global configuration object
            builder: a callable which gets passed to each call to `server.watch`

        Returns:
            `livereload.Server` instance
        """
        return server

    # Global events

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """
        The `config` event is the first event called on build and is run immediately
        after the user configuration is loaded and validated. Any alterations to the
        config should be made here.

        Args:
            config: global configuration object

        Returns:
            global configuration object
        """
        return config

    def on_pre_build(self, *, config: MkDocsConfig) -> None:
        """
        The `pre_build` event does not alter any variables. Use this event to call
        pre-build scripts.

        Args:
            config: global configuration object
        """

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        """
        The `files` event is called after the files collection is populated from the
        `docs_dir`. Use this event to add, remove, or alter files in the
        collection. Note that Page objects have not yet been associated with the
        file objects in the collection. Use [Page Events](plugins.md#page-events) to manipulate page
        specific data.

        Args:
            files: global files collection
            config: global configuration object

        Returns:
            global files collection
        """
        return files

    def on_nav(
        self, nav: Navigation, /, *, config: MkDocsConfig, files: Files
    ) -> Navigation | None:
        """
        The `nav` event is called after the site navigation is created and can
        be used to alter the site navigation.

        Args:
            nav: global navigation object
            config: global configuration object
            files: global files collection

        Returns:
            global navigation object
        """
        return nav

    def on_env(
        self, env: jinja2.Environment, /, *, config: MkDocsConfig, files: Files
    ) -> jinja2.Environment | None:
        """
        The `env` event is called after the Jinja template environment is created
        and can be used to alter the
        [Jinja environment](https://jinja.palletsprojects.com/en/latest/api/#jinja2.Environment).

        Args:
            env: global Jinja environment
            config: global configuration object
            files: global files collection

        Returns:
            global Jinja Environment
        """
        return env

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        """
        The `post_build` event does not alter any variables. Use this event to call
        post-build scripts.

        Args:
            config: global configuration object
        """

    def on_build_error(self, *, error: Exception) -> None:
        """
        The `build_error` event is called after an exception of any kind
        is caught by MkDocs during the build process.
        Use this event to clean things up before MkDocs terminates. Note that any other
        events which were scheduled to run after the error will have been skipped. See
        [Handling Errors](plugins.md#handling-errors) for more details.

        Args:
            error: exception raised
        """

    # Template events

    def on_pre_template(
        self, template: jinja2.Template, /, *, template_name: str, config: MkDocsConfig
    ) -> jinja2.Template | None:
        """
        The `pre_template` event is called immediately after the subject template is
        loaded and can be used to alter the template.

        Args:
            template: a Jinja2 [Template](https://jinja.palletsprojects.com/en/latest/api/#jinja2.Template) object
            template_name: string filename of template
            config: global configuration object

        Returns:
            a Jinja2 [Template](https://jinja.palletsprojects.com/en/latest/api/#jinja2.Template) object
        """
        return template

    def on_template_context(
        self, context: TemplateContext, /, *, template_name: str, config: MkDocsConfig
    ) -> TemplateContext | None:
        """
        The `template_context` event is called immediately after the context is created
        for the subject template and can be used to alter the context for that specific
        template only.

        Args:
            context: dict of template context variables
            template_name: string filename of template
            config: global configuration object

        Returns:
            dict of template context variables
        """
        return context

    def on_post_template(
        self, output_content: str, /, *, template_name: str, config: MkDocsConfig
    ) -> str | None:
        """
        The `post_template` event is called after the template is rendered, but before
        it is written to disc and can be used to alter the output of the template.
        If an empty string is returned, the template is skipped and nothing is is
        written to disc.

        Args:
            output_content: output of rendered template as string
            template_name: string filename of template
            config: global configuration object

        Returns:
            output of rendered template as string
        """
        return output_content

    # Page events

    def on_pre_page(self, page: Page, /, *, config: MkDocsConfig, files: Files) -> Page | None:
        """
        The `pre_page` event is called before any actions are taken on the subject
        page and can be used to alter the `Page` instance.

        Args:
            page: `mkdocs.structure.pages.Page` instance
            config: global configuration object
            files: global files collection

        Returns:
            `mkdocs.structure.pages.Page` instance
        """
        return page

    def on_page_read_source(self, /, *, page: Page, config: MkDocsConfig) -> str | None:
        """
        > DEPRECATED: Instead of this event, prefer one of these alternatives:
        >
        > * Since MkDocs 1.6, instead set `content_bytes`/`content_string` of a `File` inside [`on_files`][].
        > * Usually (although it's not an exact alternative), `on_page_markdown` can serve the same purpose.

        The `on_page_read_source` event can replace the default mechanism to read
        the contents of a page's source from the filesystem.

        Args:
            page: `mkdocs.structure.pages.Page` instance
            config: global configuration object

        Returns:
            The raw source for a page as unicode string. If `None` is returned, the
                default loading from a file will be performed.
        """
        return None

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """
        The `page_markdown` event is called after the page's markdown is loaded
        from file and can be used to alter the Markdown source text. The meta-
        data has been stripped off and is available as `page.meta` at this point.

        Args:
            markdown: Markdown source text of page as string
            page: `mkdocs.structure.pages.Page` instance
            config: global configuration object
            files: global files collection

        Returns:
            Markdown source text of page as string
        """
        return markdown

    def on_page_content(
        self, html: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """
        The `page_content` event is called after the Markdown text is rendered to
        HTML (but before being passed to a template) and can be used to alter the
        HTML body of the page.

        Args:
            html: HTML rendered from Markdown source as string
            page: `mkdocs.structure.pages.Page` instance
            config: global configuration object
            files: global files collection

        Returns:
            HTML rendered from Markdown source as string
        """
        return html

    def on_page_context(
        self, context: TemplateContext, /, *, page: Page, config: MkDocsConfig, nav: Navigation
    ) -> TemplateContext | None:
        """
        The `page_context` event is called after the context for a page is created
        and can be used to alter the context for that specific page only.

        Args:
            context: dict of template context variables
            page: `mkdocs.structure.pages.Page` instance
            config: global configuration object
            nav: global navigation object

        Returns:
            dict of template context variables
        """
        return context

    def on_post_page(self, output: str, /, *, page: Page, config: MkDocsConfig) -> str | None:
        """
        The `post_page` event is called after the template is rendered, but
        before it is written to disc and can be used to alter the output of the
        page. If an empty string is returned, the page is skipped and nothing is
        written to disc.

        Args:
            output: output of rendered template as string
            page: `mkdocs.structure.pages.Page` instance
            config: global configuration object

        Returns:
            output of rendered template as string
        """
        return output


EVENTS = tuple(k[3:] for k in BasePlugin.__dict__ if k.startswith("on_"))

# The above definitions were just for docs and type checking, we don't actually want them.
for k in EVENTS:
    delattr(BasePlugin, 'on_' + k)


def event_priority(priority: float) -> Callable[[T], T]:
    """
    A decorator to set an event priority for an event handler method.

    Recommended priority values:
    `100` "first", `50` "early", `0` "default", `-50` "late", `-100` "last".
    As different plugins discover more precise relations to each other, the values should be further tweaked.

    Usage example:

    ```python
    @plugins.event_priority(-100)  # Wishing to run this after all other plugins' `on_files` events.
    def on_files(self, files, config, **kwargs):
        ...
    ```

    New in MkDocs 1.4.
    Recommended shim for backwards compatibility:

    ```python
    try:
        from mkdocs.plugins import event_priority
    except ImportError:
        event_priority = lambda priority: lambda f: f  # No-op fallback
    ```
    """

    def decorator(event_method):
        event_method.mkdocs_priority = priority
        return event_method

    return decorator


class CombinedEvent(Generic[P, T]):
    """
    A descriptor that allows defining multiple event handlers and declaring them under one event's name.

    Usage example:

    ```python
    @plugins.event_priority(100)
    def _on_page_markdown_1(self, markdown: str, **kwargs):
        ...

    @plugins.event_priority(-50)
    def _on_page_markdown_2(self, markdown: str, **kwargs):
        ...

    on_page_markdown = plugins.CombinedEvent(_on_page_markdown_1, _on_page_markdown_2)
    ```

    NOTE: The names of the sub-methods **can't** start with `on_`;
    instead they can start with `_on_` like in the the above example, or anything else.
    """

    def __init__(self, *methods: Callable[Concatenate[Any, P], T]):
        self.methods = methods

    # This is only for mypy, so CombinedEvent can be a valid override of the methods in BasePlugin
    def __call__(self, instance: BasePlugin, *args: P.args, **kwargs: P.kwargs) -> T:
        raise TypeError(f"{type(self).__name__!r} object is not callable")

    def __get__(self, instance, owner=None):
        return CombinedEvent(*(f.__get__(instance, owner) for f in self.methods))


class PluginCollection(dict, MutableMapping[str, BasePlugin]):
    """
    A collection of plugins.

    In addition to being a dict of Plugin instances, each event method is registered
    upon being added. All registered methods for a given event can then be run in order
    by calling `run_event`.
    """

    _current_plugin: str | None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.events: dict[str, list[Callable]] = {k: [] for k in EVENTS}
        self._event_origins: dict[Callable, str] = {}

    def _register_event(
        self, event_name: str, method: CombinedEvent | Callable, plugin_name: str | None = None
    ) -> None:
        """Register a method for an event."""
        if isinstance(method, CombinedEvent):
            for sub in method.methods:
                self._register_event(event_name, sub, plugin_name=plugin_name)
        else:
            events = self.events[event_name]
            if event_name == 'page_read_source' and len(events) == 1:
                plugin1 = self._event_origins.get(next(iter(events)), '<unknown>')
                plugin2 = plugin_name or '<unknown>'
                log.warning(
                    "Multiple 'on_page_read_source' handlers can't work "
                    f"(both plugins '{plugin1}' and '{plugin2}' registered one)."
                )
            utils.insort(events, method, key=lambda m: -getattr(m, 'mkdocs_priority', 0))
            if plugin_name:
                try:
                    self._event_origins[method] = plugin_name
                except TypeError:  # If the method is somehow not hashable.
                    pass

    def __getitem__(self, key: str) -> BasePlugin:
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: BasePlugin) -> None:
        super().__setitem__(key, value)
        # Register all of the event methods defined for this Plugin.
        for event_name in (x for x in dir(value) if x.startswith('on_')):
            method = getattr(value, event_name, None)
            if callable(method):
                self._register_event(event_name[3:], method, plugin_name=key)

    @overload
    def run_event(self, name: str, **kwargs) -> Any:
        ...

    @overload
    def run_event(self, name: str, item: T, **kwargs) -> T:
        ...

    def run_event(self, name: str, item=None, **kwargs):
        """
        Run all registered methods of an event.

        `item` is the object to be modified or replaced and returned by the event method.
        If it isn't given the event method creates a new object to be returned.
        All other keywords are variables for context, but would not generally
        be modified by the event method.
        """
        pass_item = item is not None
        for method in self.events[name]:
            self._current_plugin = self._event_origins.get(method, '<unknown>')
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.debug(f"Running `{name}` event from plugin '{self._current_plugin}'")
            if pass_item:
                result = method(item, **kwargs)
            else:
                result = method(**kwargs)
            # keep item if method returned `None`
            if result is not None:
                item = result
        self._current_plugin = None
        return item

    def on_startup(self, *, command: Literal['build', 'gh-deploy', 'serve'], dirty: bool) -> None:
        return self.run_event('startup', command=command, dirty=dirty)

    def on_shutdown(self) -> None:
        return self.run_event('shutdown')

    def on_serve(
        self, server: LiveReloadServer, *, config: MkDocsConfig, builder: Callable
    ) -> LiveReloadServer:
        return self.run_event('serve', server, config=config, builder=builder)

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        return self.run_event('config', config)

    def on_pre_build(self, *, config: MkDocsConfig) -> None:
        return self.run_event('pre_build', config=config)

    def on_files(self, files: Files, *, config: MkDocsConfig) -> Files:
        return self.run_event('files', files, config=config)

    def on_nav(self, nav: Navigation, *, config: MkDocsConfig, files: Files) -> Navigation:
        return self.run_event('nav', nav, config=config, files=files)

    def on_env(self, env: jinja2.Environment, *, config: MkDocsConfig, files: Files):
        return self.run_event('env', env, config=config, files=files)

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        return self.run_event('post_build', config=config)

    def on_build_error(self, *, error: Exception) -> None:
        return self.run_event('build_error', error=error)

    def on_pre_template(
        self, template: jinja2.Template, *, template_name: str, config: MkDocsConfig
    ) -> jinja2.Template:
        return self.run_event('pre_template', template, template_name=template_name, config=config)

    def on_template_context(
        self, context: TemplateContext, *, template_name: str, config: MkDocsConfig
    ) -> TemplateContext:
        return self.run_event(
            'template_context', context, template_name=template_name, config=config
        )

    def on_post_template(
        self, output_content: str, *, template_name: str, config: MkDocsConfig
    ) -> str:
        return self.run_event(
            'post_template', output_content, template_name=template_name, config=config
        )

    def on_pre_page(self, page: Page, *, config: MkDocsConfig, files: Files) -> Page:
        return self.run_event('pre_page', page, config=config, files=files)

    def on_page_read_source(self, *, page: Page, config: MkDocsConfig) -> str | None:
        return self.run_event('page_read_source', page=page, config=config)

    def on_page_markdown(
        self, markdown: str, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str:
        return self.run_event('page_markdown', markdown, page=page, config=config, files=files)

    def on_page_content(self, html: str, *, page: Page, config: MkDocsConfig, files: Files) -> str:
        return self.run_event('page_content', html, page=page, config=config, files=files)

    def on_page_context(
        self, context: TemplateContext, *, page: Page, config: MkDocsConfig, nav: Navigation
    ) -> TemplateContext:
        return self.run_event('page_context', context, page=page, config=config, nav=nav)

    def on_post_page(self, output: str, *, page: Page, config: MkDocsConfig) -> str:
        return self.run_event('post_page', output, page=page, config=config)


class PrefixedLogger(logging.LoggerAdapter):
    """A logger adapter to prefix log messages."""

    def __init__(self, prefix: str, logger: logging.Logger) -> None:
        """
        Initialize the logger adapter.

        Arguments:
            prefix: The string to insert in front of every message.
            logger: The logger instance.
        """
        super().__init__(logger, {})
        self.prefix = prefix

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, Any]:
        """
        Process the message.

        Arguments:
            msg: The message:
            kwargs: Remaining arguments.

        Returns:
            The processed message.
        """
        return f"{self.prefix}: {msg}", kwargs


def get_plugin_logger(name: str) -> PrefixedLogger:
    """
    Return a logger for plugins.

    Arguments:
        name: The name to use with `logging.getLogger`.

    Returns:
        A logger configured to work well in MkDocs,
            prefixing each message with the plugin package name.

    Example:
        ```python
        from mkdocs.plugins import get_plugin_logger

        log = get_plugin_logger(__name__)
        log.info("My plugin message")
        ```
    """
    logger = logging.getLogger(f"mkdocs.plugins.{name}")
    return PrefixedLogger(name.split(".", 1)[0], logger)
