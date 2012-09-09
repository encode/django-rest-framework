"""
Helper classes for parsers.
"""
import datetime
import decimal
from django.utils import simplejson as json
from djangorestframework.compat import timezone


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time,
    decimal types, and generators.
    """
    def default(self, o):
        # For Date Time string spec, see ECMA 262
        # http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if timezone and timezone.is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif hasattr(o, '__iter__'):
            return [i for i in o]
        return super(JSONEncoder, self).default(o)
