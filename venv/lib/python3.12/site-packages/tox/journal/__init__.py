"""This module handles collecting and persisting in json format a tox session."""

from __future__ import annotations

import json
import locale
from pathlib import Path

from .env import EnvJournal
from .main import Journal


def write_journal(path: Path | None, journal: Journal) -> None:
    if path is None:
        return
    with Path(path).open("w", encoding=locale.getpreferredencoding(do_setlocale=False)) as file_handler:
        json.dump(journal.content, file_handler, indent=2, ensure_ascii=False)


__all__ = (
    "EnvJournal",
    "Journal",
    "write_journal",
)
