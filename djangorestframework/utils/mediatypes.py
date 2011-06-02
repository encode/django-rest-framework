"""
Handling of media types, as found in HTTP Content-Type and Accept headers.

See http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.7
"""

from django.http.multipartparser import parse_header


def media_type_matches(lhs, rhs):
    """
    Returns ``True`` if the media type in the first argument <= the
    media type in the second argument.  The media types are strings
    as described by the HTTP spec.

    Valid media type strings include:

    'application/json; indent=4'
    'application/json'
    'text/*'
    '*/*'
    """
    lhs = _MediaType(lhs)
    rhs = _MediaType(rhs)
    return lhs.match(rhs)


def is_form_media_type(media_type):
    """
    Return True if the media type is a valid form media type as defined by the HTML4 spec.
    (NB. HTML5 also adds text/plain to the list of valid form media types, but we don't support this here)
    """
    media_type = _MediaType(media_type)
    return media_type.full_type == 'application/x-www-form-urlencoded' or \
           media_type.full_type == 'multipart/form-data'


def add_media_type_param(media_type, key, val):
    """
    Add a key, value parameter to a media type string, and return the new media type string.
    """
    media_type = _MediaType(media_type)
    media_type.params[key] = val
    return str(media_type)


def get_media_type_params(media_type):
    """
    Return a dictionary of the parameters on the given media type.
    """
    return _MediaType(media_type).params


def order_by_precedence(media_type_lst):
    """
    Returns a list of lists of media type strings, ordered by precedence.
    Precedence is determined by how specific a media type is:

    3. 'type/subtype; param=val'
    2. 'type/subtype'
    1. 'type/*'
    0. '*/*'
    """
    ret = [[],[],[],[]]
    for media_type in media_type_lst:
        precedence = _MediaType(media_type).precedence
        ret[3-precedence].append(media_type)
    return ret


class _MediaType(object):
    def __init__(self, media_type_str):
        if media_type_str is None:
            media_type_str = ''
        self.orig = media_type_str
        self.full_type, self.params = parse_header(media_type_str)
        self.main_type, sep, self.sub_type = self.full_type.partition('/')

    def match(self, other):
        """Return true if this MediaType satisfies the given MediaType."""
        for key in self.params.keys():
            if key != 'q' and other.params.get(key, None) != self.params.get(key, None):
                return False

        if self.sub_type != '*' and other.sub_type != '*'  and other.sub_type != self.sub_type:
            return False

        if self.main_type != '*' and other.main_type != '*' and other.main_type != self.main_type:
            return False

        return True

    @property
    def precedence(self):
        """
        Return a precedence level from 0-3 for the media type given how specific it is.
        """
        if self.main_type == '*':
            return 0
        elif self.sub_type == '*':
            return 1
        elif not self.params or self.params.keys() == ['q']:
            return 2
        return 3

    #def quality(self):
    #    """
    #    Return a quality level for the media type.
    #    """
    #    try:
    #        return Decimal(self.params.get('q', '1.0'))
    #    except:
    #        return Decimal(0)
 
    #def score(self):
    #    """
    #    Return an overall score for a given media type given it's quality and precedence.
    #    """
    #    # NB. quality values should only have up to 3 decimal points
    #    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.9
    #    return self.quality * 10000 + self.precedence
    
    #def as_tuple(self):
    #    return (self.main_type, self.sub_type, self.params)

    #def __repr__(self):
    #    return "<MediaType %s>" % (self.as_tuple(),)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        ret = "%s/%s" % (self.main_type, self.sub_type)
        for key, val in self.params.items():
            ret += "; %s=%s" % (key, val)
        return ret

