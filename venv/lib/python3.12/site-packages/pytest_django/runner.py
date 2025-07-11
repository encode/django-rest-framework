from argparse import ArgumentParser
from typing import Any, Iterable


class TestRunner:
    """A Django test runner which uses pytest to discover and run tests when using `manage.py test`."""

    def __init__(
        self,
        *,
        verbosity: int = 1,
        failfast: bool = False,
        keepdb: bool = False,
        **kwargs: Any,
    ) -> None:
        self.verbosity = verbosity
        self.failfast = failfast
        self.keepdb = keepdb

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--keepdb", action="store_true", help="Preserves the test DB between runs."
        )

    def run_tests(self, test_labels: Iterable[str], **kwargs: Any) -> int:
        """Run pytest and return the exitcode.

        It translates some of Django's test command option to pytest's.
        """
        import pytest

        argv = []
        if self.verbosity == 0:
            argv.append("--quiet")
        elif self.verbosity >= 2:
            verbosity = "v" * (self.verbosity - 1)
            argv.append(f"-{verbosity}")
        if self.failfast:
            argv.append("--exitfirst")
        if self.keepdb:
            argv.append("--reuse-db")

        argv.extend(test_labels)
        return pytest.main(argv)
