#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform
from optparse import OptionParser
from urllib3.exceptions import SSLError

import txclib
from txclib import utils
from txclib.log import set_log_level, logger
from txclib.exceptions import AuthenticationError


# use pyOpenSSL if available
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except ImportError:
    pass


# This block ensures that ^C interrupts are handled quietly.
try:
    import signal

    def exithandler(signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        sys.exit(1)

    signal.signal(signal.SIGINT, exithandler)
    signal.signal(signal.SIGTERM, exithandler)
    if hasattr(signal, 'SIGPIPE'):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

except KeyboardInterrupt:
    sys.exit(1)

# In python 3 default encoding is utf-8
if sys.version_info < (3, 0):
    reload(sys)  # WTF? Otherwise setdefaultencoding doesn't work
    # When we open file with f = codecs.open we specify
    # FROM what encoding to read.
    # This sets the encoding for the strings which are created with f.read()
    sys.setdefaultencoding('utf-8')


def main(argv=None):
    """
    Here we parse the flags (short, long) and we instantiate the classes.
    """
    if argv is None:
        argv = sys.argv[1:]
    usage = "usage: %prog [options] command [cmd_options]"
    description = "This is the Transifex command line client which"\
                  " allows you to manage your translations locally and sync"\
                  " them with the master Transifex server.\nIf you'd like to"\
                  " check the available commands issue `%prog help` or if you"\
                  " just want help with a specific command issue `%prog help"\
                  " command`"
    version = '%s, py %s.%s, %s' % (
        txclib.__version__,
        sys.version_info.major,
        sys.version_info.minor,
        platform.machine()
    )
    parser = OptionParser(
        usage=usage, version=version, description=description
    )
    parser.disable_interspersed_args()
    parser.add_option(
        "-d", "--debug", action="store_true", dest="debug",
        default=False, help=("enable debug messages")
    )
    parser.add_option(
        "-q", "--quiet", action="store_true", dest="quiet",
        default=False, help="don't print status messages to stdout"
    )
    parser.add_option(
        "-r", "--root", action="store", dest="root_dir", type="string",
        default=None, help="change root directory (default is cwd)"
    )
    parser.add_option(
        "--traceback", action="store_true", dest="trace", default=False,
        help="print full traceback on exceptions"
    )
    parser.add_option(
        "--disable-colors", action="store_true", dest="color_disable",
        default=(os.name == 'nt' or not sys.stdout.isatty()),
        help="disable colors in the output of commands"
    )
    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.error("No command was given")

    utils.DISABLE_COLORS = options.color_disable

    # set log level
    if options.quiet:
        set_log_level('WARNING')
    elif options.debug:
        set_log_level('DEBUG')

    # find .tx
    path_to_tx = options.root_dir or utils.find_dot_tx()

    cmd = args[0]
    try:
        utils.exec_command(cmd, args[1:], path_to_tx)
    except SSLError as e:
        logger.error("SSl error %s" % e)
        sys.exit(1)
    except utils.UnknownCommandError:
        logger.error("Command %s not found" % cmd)
        sys.exit(1)
    except AuthenticationError:
        authentication_failed_message = """
Error: Authentication failed. Please make sure your credentials are valid. You
can update your credentials in the ~/.transifexrc file. For more information,
visit https://docs.transifex.com/client/client-configuration#-transifexrc.
"""
        logger.error(authentication_failed_message)
    except Exception:
        import traceback
        if options.trace:
            traceback.print_exc()
        else:
            formatted_lines = traceback.format_exc().splitlines()
            logger.error(formatted_lines[-1])
        sys.exit(1)


# Run baby :) ... run
if __name__ == "__main__":
    # sys.argv[0] is the name of the script that we’re running.
    main()
