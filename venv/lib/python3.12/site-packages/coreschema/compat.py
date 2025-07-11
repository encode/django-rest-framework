import sys

if sys.version_info.major == 2:
    text_types = (str, unicode)
    numeric_types = (float, int, long)
else:
    text_types = (str,)
    numeric_types = (float, int)
