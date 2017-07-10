
from __future__ import absolute_import

import functools
import json  # noqa


def strict_constant(o):
    raise ValueError('Out of range float values are not JSON compliant: ' + repr(o))


@functools.wraps(json.dump)
def dump(*args, **kwargs):
    kwargs.setdefault('allow_nan', False)
    return json.dump(*args, **kwargs)


@functools.wraps(json.dumps)
def dumps(*args, **kwargs):
    kwargs.setdefault('allow_nan', False)
    return json.dumps(*args, **kwargs)


@functools.wraps(json.load)
def load(*args, **kwargs):
    kwargs.setdefault('parse_constant', strict_constant)
    return json.load(*args, **kwargs)


@functools.wraps(json.loads)
def loads(*args, **kwargs):
    kwargs.setdefault('parse_constant', strict_constant)
    return json.loads(*args, **kwargs)
