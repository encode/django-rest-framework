from django.conf.urls.defaults import url
from djangorestframework.settings import api_settings


def format_suffix_patterns(urlpatterns, suffix_required=False, suffix_kwarg=None):
    """
    Supplement existing urlpatterns with corrosponding patterns that also
    include a '.format' suffix.  Retains urlpattern ordering.
    """
    suffix_kwarg = suffix_kwarg or api_settings.FORMAT_SUFFIX_KWARG
    suffix_pattern = '.(?P<%s>[a-z]+)$' % suffix_kwarg

    ret = []
    for urlpattern in urlpatterns:
        # Form our complementing '.format' urlpattern
        regex = urlpattern.regex.pattern.rstrip('$') + suffix_pattern
        view = urlpattern._callback or urlpattern._callback_str
        kwargs = urlpattern.default_args
        name = urlpattern.name
        # Add in both the existing and the new urlpattern
        if not suffix_required:
            ret.append(urlpattern)
        ret.append(url(regex, view, kwargs, name))
    return ret
