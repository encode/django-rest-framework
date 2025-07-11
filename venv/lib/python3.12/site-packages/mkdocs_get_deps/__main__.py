from __future__ import annotations

import argparse
import logging
import sys

from . import get_deps, get_projects_file

parser = argparse.ArgumentParser(
    description="Show required PyPI packages inferred from plugins in mkdocs.yml."
)
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
parser.add_argument(
    "-f",
    "--config-file",
    type=argparse.FileType("r"),
    help="Provide a specific MkDocs config. This can be a file name, or '-' to read from stdin.",
    default=None,
)
parser.add_argument(
    "-p",
    "--projects-file",
    help="URL or local path of the registry file that declares all known MkDocs-related projects.",
    default="https://raw.githubusercontent.com/mkdocs/catalog/main/projects.yaml",
)


class CountHandler(logging.NullHandler):
    warning_count = 0

    def handle(self, record):
        rv = self.filter(record)
        if rv:
            self.warning_count += 1
        return rv


def cli():
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s - mkdocs-get-deps: %(message)s",
    )

    warning_counter = CountHandler()
    warning_counter.setLevel(logging.WARNING)
    logging.getLogger("mkdocs").addHandler(warning_counter)

    with get_projects_file(args.projects_file) as projects_file:
        deps = get_deps(config_file=args.config_file, projects_file=projects_file)

    for dep in deps:
        print(dep)  # noqa: T201

    if warning_counter.warning_count:
        sys.exit(1)


if __name__ == "__main__":
    cli()
