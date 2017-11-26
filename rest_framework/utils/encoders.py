"""
Helper classes for parsers.
"""
from __future__ import absolute_import, unicode_literals

import datetime
import decimal
import json  # noqa
import uuid

from django.db.models.query import QuerySet
from django.utils import six, timezone
from django.utils.encoding import force_text
from django.utils.functional import Promise

from rest_framework.compat import coreapi


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time/timedelta,
    decimal types, generators and other basic python objects.
    """
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
            return representation
        elif isinstance(obj, datetime.timedelta):
            return six.text_type(obj.total_seconds())
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
        elif (coreapi is not None) and isinstance(obj, (coreapi.Document, coreapi.Error)):
            raise RuntimeError(
                'Cannot return a coreapi object from a JSON view. '
                'You should be using a schema renderer instead for this view.'
            )
        elif hasattr(obj, '__getitem__'):
            try:
                return dict(obj)
            except Exception:
                pass
        elif hasattr(obj, '__iter__'):
            return tuple(item for item in obj)
        return super(JSONEncoder, self).default(obj)
