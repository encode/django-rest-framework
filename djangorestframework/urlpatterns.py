from django.conf.urls.defaults import url


def format_suffix_patterns(urlpatterns, suffix_required=False):
    """
    Supplement existing urlpatterns with corrosponding patterns that also
    include a '.format' suffix.  Retains urlpattern ordering.
    """
    ret = []
    for urlpattern in urlpatterns:
        # Form our complementing '.format' urlpattern
        regex = urlpattern.regex.pattern.rstrip('$') + '.(?P<format>[a-z]+)$'
        view = urlpattern._callback or urlpattern._callback_str
        kwargs = urlpattern.default_args
        name = urlpattern.name
        # Add in both the existing and the new urlpattern
        if not suffix_required:
            ret.append(urlpattern)
        ret.append(url(regex, view, kwargs, name))
    return ret
