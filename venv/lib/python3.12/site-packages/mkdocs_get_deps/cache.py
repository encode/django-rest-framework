from __future__ import annotations

import datetime
import hashlib
import logging
import os
import random
import urllib.request
from typing import Callable

import platformdirs

from . import __version__

log = logging.getLogger(f"mkdocs.{__name__}")


def _download_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"mkdocs-get-deps/{__version__}"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def download_and_cache_url(
    url: str,
    cache_duration: datetime.timedelta,
    *,
    download: Callable[[str], bytes] = _download_url,
    comment: bytes = b"# ",
) -> bytes:
    """Downloads a file from the URL, stores it under ~/.cache/, and returns its content.

    For tracking the age of the content, a prefix is inserted into the stored file, rather than relying on mtime.

    Args:
        url: URL to use.
        download: Callback that will accept the URL and actually perform the download.
        cache_duration: How long to consider the URL content cached.
        comment: The appropriate comment prefix for this file format.
    """
    directory = os.path.join(platformdirs.user_cache_dir("mkdocs"), "mkdocs_url_cache")
    name_hash = hashlib.sha256(url.encode()).hexdigest()[:32]
    path = os.path.join(directory, name_hash + os.path.splitext(url)[1])

    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    prefix = b"%s%s downloaded at timestamp " % (comment, url.encode())
    # Check for cached file and try to return it
    if os.path.isfile(path):
        try:
            with open(path, "rb") as f:
                line = f.readline()
                if line.startswith(prefix):
                    line = line[len(prefix) :]
                    timestamp = int(line)
                    if datetime.timedelta(seconds=(now - timestamp)) <= cache_duration:
                        log.debug(f"Using cached '{path}' for '{url}'")
                        return f.read()
        except (OSError, ValueError) as e:
            log.debug(f"{type(e).__name__}: {e}")

    # Download and cache the file
    log.debug(f"Downloading '{url}' to '{path}'")
    content = download(url)
    os.makedirs(directory, exist_ok=True)
    temp_filename = f"{path}.{random.randrange(1 << 32):08x}.part"
    with open(temp_filename, "wb") as f:
        f.write(b"%s%d\n" % (prefix, now))
        f.write(content)
    os.replace(temp_filename, path)
    return content
