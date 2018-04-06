r"""
______ _____ _____ _____    __
| ___ \  ___/  ___|_   _|  / _|                                           | |
| |_/ / |__ \ `--.  | |   | |_ _ __ __ _ _ __ ___   _____      _____  _ __| |__
|    /|  __| `--. \ | |   |  _| '__/ _` | '_ ` _ \ / _ \ \ /\ / / _ \| '__| |/ /
| |\ \| |___/\__/ / | |   | | | | | (_| | | | | | |  __/\ V  V / (_) | |  |   <
\_| \_\____/\____/  \_/   |_| |_|  \__,_|_| |_| |_|\___| \_/\_/ \___/|_|  |_|\_|
"""

__title__ = 'Django REST framework'
__version__ = '3.8.2'
__author__ = 'Tom Christie'
__license__ = 'BSD 2-Clause'
__copyright__ = 'Copyright 2011-2018 Tom Christie'

# Version synonym
VERSION = __version__

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = 'iso-8859-1'

# Default datetime input and output formats
ISO_8601 = 'iso-8601'

default_app_config = 'rest_framework.apps.RestFrameworkConfig'
