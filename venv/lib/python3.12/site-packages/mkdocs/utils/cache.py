import datetime
import urllib.request
from typing import Callable

import mkdocs_get_deps.cache

import mkdocs


def download_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"mkdocs/{mkdocs.__version__}"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def download_and_cache_url(
    url: str,
    cache_duration: datetime.timedelta,
    *,
    download: Callable[[str], bytes] = download_url,
    comment: bytes = b"# ",
) -> bytes:
    """
    Downloads a file from the URL, stores it under ~/.cache/, and returns its content.

    For tracking the age of the content, a prefix is inserted into the stored file, rather than relying on mtime.

    Args:
        url: URL to use.
        download: Callback that will accept the URL and actually perform the download.
        cache_duration: How long to consider the URL content cached.
        comment: The appropriate comment prefix for this file format.
    """
    return mkdocs_get_deps.cache.download_and_cache_url(
        url=url, cache_duration=cache_duration, download=download, comment=comment
    )
