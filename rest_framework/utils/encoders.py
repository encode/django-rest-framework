"""
Helper classes for parsers.
"""
import datetime
import decimal
import json  # noqa
import uuid

from django.conf import settings
from django.db.models.query import QuerySet
from django.test.client import encode_file
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.functional import Promise
from django.utils.itercompat import is_iterable

from rest_framework.compat import coreapi


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time/timedelta,
    decimal types, generators and other basic python objects.
    """
    def default(self, obj):
        # For Date Time string spec, see ECMA 262
        # https://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(obj, Promise):
            return force_str(obj)
        elif isinstance(obj, datetime.datetime):
            representation = obj.isoformat()
            if representation.endswith('+00:00'):
                representation = representation[:-6] + 'Z'
            return representation
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            if timezone and timezone.is_aware(obj):
                raise ValueError("JSON can't represent timezone-aware times.")
            representation = obj.isoformat()
            return representation
        elif isinstance(obj, datetime.timedelta):
            return str(obj.total_seconds())
        elif isinstance(obj, decimal.Decimal):
            # Serializers will coerce decimals to strings by default.
            return float(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, QuerySet):
            return tuple(obj)
        elif isinstance(obj, bytes):
            # Best-effort for binary blobs. See #4187.
            return obj.decode()
        elif hasattr(obj, 'tolist'):
            # Numpy arrays and array scalars.
            return obj.tolist()
        elif (coreapi is not None) and isinstance(obj, (coreapi.Document, coreapi.Error)):
            raise RuntimeError(
                'Cannot return a coreapi object from a JSON view. '
                'You should be using a schema renderer instead for this view.'
            )
        elif hasattr(obj, '__getitem__'):
            cls = (list if isinstance(obj, (list, tuple)) else dict)
            try:
                return cls(obj)
            except Exception:
                pass
        elif hasattr(obj, '__iter__'):
            return tuple(item for item in obj)
        return super().default(obj)


class NestedMultiPartEncoder:
    def encode(self, boundary, data):
        lines = []

        def to_bytes(s):
            return force_bytes(s, settings.DEFAULT_CHARSET)

        def is_file(thing):
            return hasattr(thing, "read") and callable(thing.read)

        def to_lines(d, prefix='', dot='.'):
            for (key, value) in d.items():
                if prefix:
                    key = '{prefix}{dot}{key}'

                if value is None:
                    raise TypeError(
                        'Cannot encode None as POST data. Did you mean to pass an '
                        'empty string or omit the value?'
                    )
                elif isinstance(value, dict):
                    to_lines(value, key)
                elif is_file(value):
                    lines.extend(encode_file(boundary, key, value))
                elif not isinstance(value, str) and is_iterable(value):
                    for index, item in enumerate(value):
                        if isinstance(item, dict):
                            to_lines(item, f'{key}[{index}]', '')
                        elif is_file(item):
                            lines.extend(encode_file(boundary, f'{key}{[index]}', item))
                        else:
                            lines.extend(to_bytes(val) for val in [
                                f'--{boundary}',
                                f'Content-Disposition: form-data; name="{key}{[index]}"',
                                '',
                                item
                            ])
                else:
                    lines.extend(to_bytes(val) for val in [
                        '--%s' % boundary,
                        'Content-Disposition: form-data; name="%s"' % key,
                        '',
                        value
                    ])

        to_lines(data)

        lines.extend([
            to_bytes('--%s--' % boundary),
            b'',
        ])
        return b'\r\n'.join(lines)
