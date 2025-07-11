# coding: utf-8
from coreapi.codecs.base import BaseCodec
from coreapi.compat import urlparse
from coreapi.utils import DownloadedFile, guess_extension
import cgi
import os
import posixpath
import tempfile


def _unique_output_path(path):
    """
    Given a path like '/a/b/c.txt'

    Return the first available filename that doesn't already exist,
    using an incrementing suffix if needed.

    For example: '/a/b/c.txt' or '/a/b/c (1).txt' or '/a/b/c (2).txt'...
    """
    basename, ext = os.path.splitext(path)
    idx = 0
    while os.path.exists(path):
        idx += 1
        path = "%s (%d)%s" % (basename, idx, ext)
    return path


def _safe_filename(filename):
    """
    Sanitize output filenames, to remove any potentially unsafe characters.
    """
    filename = os.path.basename(filename)

    keepcharacters = (' ', '.', '_', '-')
    filename = ''.join(
        char for char in filename
        if char.isalnum() or char in keepcharacters
    ).strip().strip('.')

    return filename


def _get_filename_from_content_disposition(content_disposition):
    """
    Determine an output filename based on the `Content-Disposition` header.
    """
    params = value, params = cgi.parse_header(content_disposition)

    if 'filename*' in params:
        try:
            charset, lang, filename = params['filename*'].split('\'', 2)
            filename = urlparse.unquote(filename)
            filename = filename.encode('iso-8859-1').decode(charset)
            return _safe_filename(filename)
        except (ValueError, LookupError):
            pass

    if 'filename' in params:
        filename = params['filename']
        return _safe_filename(filename)

    return None


def _get_filename_from_url(url, content_type=None):
    """
    Determine an output filename based on the download URL.
    """
    parsed = urlparse.urlparse(url)
    final_path_component = posixpath.basename(parsed.path.rstrip('/'))
    filename = _safe_filename(final_path_component)
    suffix = guess_extension(content_type or '')

    if filename:
        if '.' not in filename:
            return filename + suffix
        return filename
    elif suffix:
        return 'download' + suffix

    return None


def _get_filename(base_url=None, content_type=None, content_disposition=None):
    """
    Determine an output filename to use for the download.
    """
    filename = None
    if content_disposition:
        filename = _get_filename_from_content_disposition(content_disposition)
    if base_url and not filename:
        filename = _get_filename_from_url(base_url, content_type)
    if not filename:
        return None  # Ensure empty filenames return as `None` for consistency.
    return filename


class DownloadCodec(BaseCodec):
    """
    A codec to handle raw file downloads, such as images and other media.
    """
    media_type = '*/*'
    format = 'download'

    def __init__(self, download_dir=None):
        """
        `download_dir` - The path to use for file downloads.
        """
        self._delete_on_close = download_dir is None
        self._download_dir = download_dir

    @property
    def download_dir(self):
        return self._download_dir

    def decode(self, bytestring, **options):
        base_url = options.get('base_url')
        content_type = options.get('content_type')
        content_disposition = options.get('content_disposition')

        # Write the download to a temporary .download file.
        fd, temp_path = tempfile.mkstemp(suffix='.download')
        file_handle = os.fdopen(fd, 'wb')
        file_handle.write(bytestring)
        file_handle.close()

        # Determine the output filename.
        output_filename = _get_filename(base_url, content_type, content_disposition)
        if output_filename is None:
            output_filename = os.path.basename(temp_path)

        # Determine the output directory.
        output_dir = self._download_dir
        if output_dir is None:
            output_dir = os.path.dirname(temp_path)

        # Determine the full output path.
        output_path = os.path.join(output_dir, output_filename)

        # Move the temporary download file to the final location.
        if output_path != temp_path:
            output_path = _unique_output_path(output_path)
            os.rename(temp_path, output_path)

        # Open the file and return the file object.
        output_file = open(output_path, 'rb')
        downloaded = DownloadedFile(output_file, output_path, delete=self._delete_on_close)
        downloaded.basename = output_filename
        return downloaded
