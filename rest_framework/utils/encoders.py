"""
Helper classes for parsers.
"""
from __future__ import unicode_literals

import datetime
import decimal
import json
from json.encoder import (FLOAT_REPR, INFINITY, c_make_encoder, 
                          encode_basestring_ascii, encode_basestring, 
                          _make_iterencode)
import uuid

from django.db.models.query import QuerySet
from django.utils import six, timezone
from django.utils.encoding import force_text
from django.utils.functional import Promise

from rest_framework.compat import coreapi, total_seconds


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time/timedelta,
    decimal types, generators and other basic python objects.
    """

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string
        representation as available.
        For example::
            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)
        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring
        if six.PY2:
            if self.encoding != 'utf-8':
                def _encoder(o, _orig_encoder=_encoder,
                             _encoding=self.encoding):
                    if isinstance(o, str):
                        o = o.decode(_encoding)
                    return _orig_encoder(o)

        if self.encoding != 'utf-8':
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, str):
                    o = o.decode(_encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan,
                _repr=FLOAT_REPR, _inf=INFINITY, _neginf=-INFINITY):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = 'null'
            elif o == _inf:
                text = 'null'
            elif o == _neginf:
                text = 'null'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text


        if (_one_shot and c_make_encoder is not None
                and self.indent is None):
            _iterencode = c_make_encoder(
                markers, self.default, _encoder, self.indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan)
        else:
            _iterencode = _make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot)
        return _iterencode(o, 0)

    def default(self, obj):
        # For Date Time string spec, see ECMA 262
        # http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(obj, Promise):
            return force_text(obj)
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
            if obj.microsecond:
                representation = representation[:12]
            return representation
        elif isinstance(obj, datetime.timedelta):
            return six.text_type(total_seconds(obj))
        elif isinstance(obj, decimal.Decimal):
            # Serializers will coerce decimals to strings by default.
            return float(obj)
        elif isinstance(obj, uuid.UUID):
            return six.text_type(obj)
        elif isinstance(obj, QuerySet):
            return tuple(obj)
        elif isinstance(obj, six.binary_type):
            # Best-effort for binary blobs. See #4187.
            return obj.decode('utf-8')
        elif hasattr(obj, 'tolist'):
            # Numpy arrays and array scalars.
            return obj.tolist()
        elif (coreapi is not None) and isinstance(obj, (coreapi.Document, 
                                                        coreapi.Error)):
            raise RuntimeError(
                'Cannot return a coreapi object from a JSON view. '
                'You should be using a schema renderer instead for this view.'
            )
        elif hasattr(obj, '__getitem__'):
            try:
                return dict(obj)
            except:
                pass
        elif hasattr(obj, '__iter__'):
            return tuple(item for item in obj)
        return super(JSONEncoder, self).default(obj)
