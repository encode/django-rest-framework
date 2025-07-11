#!/usr/bin/env python

from __future__ import annotations

import logging
import os
import shutil
import sys
import textwrap
import traceback
import warnings

import click

from mkdocs import __version__, config, utils

if sys.platform.startswith("win"):
    try:
        import colorama
    except ImportError:
        pass
    else:
        colorama.init()

log = logging.getLogger(__name__)


def _showwarning(message, category, filename, lineno, file=None, line=None):
    try:
        # Last stack frames:
        # * ...
        # * Location of call to deprecated function   <-- include this
        # * Location of call to warn()                <-- include this
        # * (stdlib) Location of call to showwarning function
        # * (this function) Location of call to extract_stack()
        stack = [frame for frame in traceback.extract_stack() if frame.line][-4:-2]
        # Make sure the actual affected file's name is still present (the case of syntax warning):
        if not any(frame.filename == filename for frame in stack):
            stack = stack[-1:] + [traceback.FrameSummary(filename, lineno, '')]

        tb = ''.join(traceback.format_list(stack))
    except Exception:
        tb = f'  File "{filename}", line {lineno}'

    log.info(f'{category.__name__}: {message}\n{tb}')


def _enable_warnings():
    from mkdocs.commands import build

    build.log.addFilter(utils.DuplicateFilter())

    warnings.simplefilter('module', DeprecationWarning)
    warnings.showwarning = _showwarning


class ColorFormatter(logging.Formatter):
    colors = {
        'CRITICAL': 'red',
        'ERROR': 'red',
        'WARNING': 'yellow',
        'DEBUG': 'blue',
    }

    text_wrapper = textwrap.TextWrapper(
        width=shutil.get_terminal_size(fallback=(0, 0)).columns,
        replace_whitespace=False,
        break_long_words=False,
        break_on_hyphens=False,
        initial_indent=' ' * 11,
        subsequent_indent=' ' * 11,
    )

    def format(self, record):
        message = super().format(record)
        prefix = f'{record.levelname:<8}-  '
        if record.levelname in self.colors:
            prefix = click.style(prefix, fg=self.colors[record.levelname])
        if self.text_wrapper.width:
            # Only wrap text if a terminal width was detected
            msg = '\n'.join(self.text_wrapper.fill(line) for line in message.splitlines())
            # Prepend prefix after wrapping so that color codes don't affect length
            return prefix + msg[11:]
        return prefix + message


class State:
    """Maintain logging level."""

    def __init__(self, log_name='mkdocs', level=logging.INFO):
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        self.stream = logging.StreamHandler()
        self.stream.setFormatter(ColorFormatter())
        self.stream.name = 'MkDocsStreamHandler'
        self.logger.addHandler(self.stream)

    def __del__(self):
        self.logger.removeHandler(self.stream)


pass_state = click.make_pass_decorator(State, ensure=True)

clean_help = "Remove old files from the site_dir before building (the default)."
config_help = (
    "Provide a specific MkDocs config. This can be a file name, or '-' to read from stdin."
)
dev_addr_help = "IP address and port to serve documentation locally (default: localhost:8000)"
serve_open_help = "Open the website in a Web browser after the initial build finishes."
strict_help = "Enable strict mode. This will cause MkDocs to abort the build on any warnings."
theme_help = "The theme to use when building your documentation."
theme_choices = sorted(utils.get_theme_names())
site_dir_help = "The directory to output the result of the documentation build."
use_directory_urls_help = "Use directory URLs when building pages (the default)."
reload_help = "Enable the live reloading in the development server (this is the default)"
no_reload_help = "Disable the live reloading in the development server."
serve_dirty_help = "Only re-build files that have changed."
serve_clean_help = (
    "Build the site without any effects of `mkdocs serve` - pure `mkdocs build`, then serve."
)
commit_message_help = (
    "A commit message to use when committing to the "
    "GitHub Pages remote branch. Commit {sha} and MkDocs {version} are available as expansions"
)
remote_branch_help = (
    "The remote branch to commit to for GitHub Pages. This "
    "overrides the value specified in config"
)
remote_name_help = (
    "The remote name to commit to for GitHub Pages. This overrides the value specified in config"
)
force_help = "Force the push to the repository."
no_history_help = "Replace the whole Git history with one new commit."
ignore_version_help = (
    "Ignore check that build is not being deployed with an older version of MkDocs."
)
watch_theme_help = (
    "Include the theme in list of files to watch for live reloading. "
    "Ignored when live reload is not used."
)
shell_help = "Use the shell when invoking Git."
watch_help = "A directory or file to watch for live reloading. Can be supplied multiple times."
projects_file_help = (
    "URL or local path of the registry file that declares all known MkDocs-related projects."
)


def add_options(*opts):
    def inner(f):
        for i in reversed(opts):
            f = i(f)
        return f

    return inner


def verbose_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(State)
        if value:
            state.logger.setLevel(logging.DEBUG)

    return click.option(
        '-v',
        '--verbose',
        is_flag=True,
        expose_value=False,
        help='Enable verbose output',
        callback=callback,
    )(f)


def quiet_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(State)
        if value:
            state.logger.setLevel(logging.ERROR)

    return click.option(
        '-q',
        '--quiet',
        is_flag=True,
        expose_value=False,
        help='Silence warnings',
        callback=callback,
    )(f)


def color_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(State)
        if value is False or (
            value is None
            and (
                not sys.stdout.isatty()
                or os.environ.get('NO_COLOR')
                or os.environ.get('TERM') == 'dumb'
            )
        ):
            state.stream.setFormatter(logging.Formatter('%(levelname)-8s-  %(message)s'))

    return click.option(
        '--color/--no-color',
        is_flag=True,
        default=None,
        expose_value=False,
        help="Force enable or disable color and wrapping for the output. Default is auto-detect.",
        callback=callback,
    )(f)


common_options = add_options(quiet_option, verbose_option)
common_config_options = add_options(
    click.option('-f', '--config-file', type=click.File('rb'), help=config_help),
    # Don't override config value if user did not specify --strict flag
    # Conveniently, load_config drops None values
    click.option('-s', '--strict/--no-strict', is_flag=True, default=None, help=strict_help),
    click.option('-t', '--theme', type=click.Choice(theme_choices), help=theme_help),
    # As with --strict, set the default to None so that this doesn't incorrectly
    # override the config file
    click.option(
        '--use-directory-urls/--no-directory-urls',
        is_flag=True,
        default=None,
        help=use_directory_urls_help,
    ),
)

PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

PKG_DIR = os.path.dirname(os.path.abspath(__file__))


@click.group(context_settings=dict(help_option_names=['-h', '--help'], max_content_width=120))
@click.version_option(
    __version__,
    '-V',
    '--version',
    message=f'%(prog)s, version %(version)s from { PKG_DIR } (Python { PYTHON_VERSION })',
)
@common_options
@color_option
def cli():
    """MkDocs - Project documentation with Markdown."""


@cli.command(name="serve")
@click.option('-a', '--dev-addr', help=dev_addr_help, metavar='<IP:PORT>')
@click.option('-o', '--open', 'open_in_browser', help=serve_open_help, is_flag=True)
@click.option('--no-livereload', 'livereload', flag_value=False, help=no_reload_help)
@click.option('--livereload', 'livereload', flag_value=True, default=True, hidden=True)
@click.option('--dirtyreload', 'build_type', flag_value='dirty', hidden=True)
@click.option('--dirty', 'build_type', flag_value='dirty', help=serve_dirty_help)
@click.option('-c', '--clean', 'build_type', flag_value='clean', help=serve_clean_help)
@click.option('--watch-theme', help=watch_theme_help, is_flag=True)
@click.option(
    '-w', '--watch', help=watch_help, type=click.Path(exists=True), multiple=True, default=[]
)
@common_config_options
@common_options
def serve_command(**kwargs):
    """Run the builtin development server."""
    from mkdocs.commands import serve

    _enable_warnings()
    serve.serve(**kwargs)


@cli.command(name="build")
@click.option('-c', '--clean/--dirty', is_flag=True, default=True, help=clean_help)
@common_config_options
@click.option('-d', '--site-dir', type=click.Path(), help=site_dir_help)
@common_options
def build_command(clean, **kwargs):
    """Build the MkDocs documentation."""
    from mkdocs.commands import build

    _enable_warnings()
    cfg = config.load_config(**kwargs)
    cfg.plugins.on_startup(command='build', dirty=not clean)
    try:
        build.build(cfg, dirty=not clean)
    finally:
        cfg.plugins.on_shutdown()


@cli.command(name="gh-deploy")
@click.option('-c', '--clean/--dirty', is_flag=True, default=True, help=clean_help)
@click.option('-m', '--message', help=commit_message_help)
@click.option('-b', '--remote-branch', help=remote_branch_help)
@click.option('-r', '--remote-name', help=remote_name_help)
@click.option('--force', is_flag=True, help=force_help)
@click.option('--no-history', is_flag=True, help=no_history_help)
@click.option('--ignore-version', is_flag=True, help=ignore_version_help)
@click.option('--shell', is_flag=True, help=shell_help)
@common_config_options
@click.option('-d', '--site-dir', type=click.Path(), help=site_dir_help)
@common_options
def gh_deploy_command(
    clean, message, remote_branch, remote_name, force, no_history, ignore_version, shell, **kwargs
):
    """Deploy your documentation to GitHub Pages."""
    from mkdocs.commands import build, gh_deploy

    _enable_warnings()
    cfg = config.load_config(remote_branch=remote_branch, remote_name=remote_name, **kwargs)
    cfg.plugins.on_startup(command='gh-deploy', dirty=not clean)
    try:
        build.build(cfg, dirty=not clean)
    finally:
        cfg.plugins.on_shutdown()
    gh_deploy.gh_deploy(
        cfg,
        message=message,
        force=force,
        no_history=no_history,
        ignore_version=ignore_version,
        shell=shell,
    )


@cli.command(name="get-deps")
@verbose_option
@click.option('-f', '--config-file', type=click.File('rb'), help=config_help)
@click.option(
    '-p',
    '--projects-file',
    default=None,
    help=projects_file_help,
    show_default=True,
)
def get_deps_command(config_file, projects_file):
    """Show required PyPI packages inferred from plugins in mkdocs.yml."""
    from mkdocs_get_deps import get_deps, get_projects_file

    from mkdocs.config.base import _open_config_file

    warning_counter = utils.CountHandler()
    warning_counter.setLevel(logging.WARNING)
    logging.getLogger('mkdocs').addHandler(warning_counter)

    with get_projects_file(projects_file) as p:
        with _open_config_file(config_file) as f:
            deps = get_deps(config_file=f, projects_file=p)

    for dep in deps:
        print(dep)  # noqa: T201

    if warning_counter.get_counts():
        sys.exit(1)


@cli.command(name="new")
@click.argument("project_directory")
@common_options
def new_command(project_directory):
    """Create a new MkDocs project."""
    from mkdocs.commands import new

    new.new(project_directory)


if __name__ == '__main__':  # pragma: no cover
    cli()
