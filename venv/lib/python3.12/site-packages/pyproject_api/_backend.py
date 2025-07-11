"""
Handles communication on the backend side between frontend and backend.

Please keep this file Python 2.7 compatible.
See https://tox.readthedocs.io/en/rewrite/development.html#code-style-guide
"""

import importlib
import json
import locale
import os
import sys
import traceback


class MissingCommand(TypeError):  # noqa: N818
    """Missing command."""


class BackendProxy:
    def __init__(self, backend_module, backend_obj):
        self.backend_module = backend_module
        self.backend_object = backend_obj
        backend = importlib.import_module(self.backend_module)
        if self.backend_object:
            backend = getattr(backend, self.backend_object)
        self.backend = backend

    def __call__(self, name, *args, **kwargs):
        on_object = self if name.startswith("_") else self.backend
        if not hasattr(on_object, name):
            msg = f"{on_object!r} has no attribute {name!r}"
            raise MissingCommand(msg)
        return getattr(on_object, name)(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}(backend={self.backend})"

    def _exit(self):  # noqa: PLR6301
        return 0

    def _optional_hooks(self):
        return {
            k: hasattr(self.backend, k)
            for k in (
                "get_requires_for_build_sdist",
                "prepare_metadata_for_build_wheel",
                "get_requires_for_build_wheel",
                "build_editable",
                "get_requires_for_build_editable",
                "prepare_metadata_for_build_editable",
            )
        }


def flush():
    sys.stderr.flush()
    sys.stdout.flush()


def run(argv):  # noqa: C901, PLR0912, PLR0915
    reuse_process = argv[0].lower() == "true"

    try:
        backend_proxy = BackendProxy(argv[1], None if len(argv) == 2 else argv[2])  # noqa: PLR2004
    except BaseException:
        print("failed to start backend", file=sys.stderr)
        raise
    else:
        print(f"started backend {backend_proxy}", file=sys.stdout)
    finally:
        flush()  # pragma: no branch
    while True:
        content = read_line()
        if not content:
            continue
        flush()  # flush any output generated before
        try:
            # python 2 does not support loading from bytearray
            if sys.version_info[0] == 2:  # pragma: no branch # noqa: PLR2004
                content = content.decode()  # pragma: no cover
            parsed_message = json.loads(content)
            result_file = parsed_message["result"]
        except Exception:  # noqa: BLE001
            # ignore messages that are not valid JSON and contain a valid result path
            print(f"Backend: incorrect request to backend: {content}", file=sys.stderr)
            flush()
        else:
            result = {}
            try:
                cmd = parsed_message["cmd"]
                print("Backend: run command {} with args {}".format(cmd, parsed_message["kwargs"]))
                outcome = backend_proxy(parsed_message["cmd"], **parsed_message["kwargs"])
                result["return"] = outcome
                if cmd == "_exit":
                    break
            except BaseException as exception:  # noqa: BLE001
                result["code"] = exception.code if isinstance(exception, SystemExit) else 1
                result["exc_type"] = exception.__class__.__name__
                result["exc_msg"] = str(exception)
                if not isinstance(exception, MissingCommand):  # for missing command do not print stack
                    traceback.print_exc()
            finally:
                try:
                    encoding = locale.getpreferredencoding(do_setlocale=False)
                    with open(result_file, "w", encoding=encoding) as file_handler:  # noqa: PTH123
                        json.dump(result, file_handler)
                except Exception:  # noqa: BLE001
                    traceback.print_exc()
                finally:
                    # used as done marker by frontend
                    print(f"Backend: Wrote response {result} to {result_file}")
                    flush()  # pragma: no branch
        if reuse_process is False:  # pragma: no branch # no test for reuse process in root test env
            break
    return 0


def read_line(fd=0):
    # for some reason input() seems to break (hangs forever) so instead we read byte by byte the unbuffered stream
    content = bytearray()
    while True:
        char = os.read(fd, 1)
        if not char:
            if not content:
                msg = "EOF without reading anything"
                raise EOFError(msg)  # we didn't get a line at all, let the caller know
            break  # pragma: no cover
        if char == b"\n":
            break
        if char != b"\r":
            content += char
    return content


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
