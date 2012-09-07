"""
Tags to optionally include the login and logout links, depending on if the
login and logout views are in the urlconf.
"""
from django import template
from django.core.urlresolvers import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def optional_login(context):
    try:
        login_url = reverse('djangorestframework:login')
    except NoReverseMatch:
        return ''

    request = context['request']
    snippet = "<a href='%s?next=%s'>Log in</a>" % (login_url, request.path)
    return snippet


@register.simple_tag(takes_context=True)
def optional_logout(context):
    try:
        logout_url = reverse('djangorestframework:logout')
    except NoReverseMatch:
        return ''

    request = context['request']
    snippet = "<a href='%s?next=%s'>Log out</a>" % (logout_url, request.path)
    return snippet
