"""
``django-guardian`` template tags. To use in a template just put the following
*load* tag inside a template::

    {% load guardian_tags %}

"""
from django import template
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group

from guardian.core import ObjectPermissionChecker
from guardian.exceptions import NotUserNorGroup

register = template.Library()


class ObjectPermissionsNode(template.Node):

    def __init__(self, for_whom, obj, context_var, checker=None):
        self.for_whom = template.Variable(for_whom)
        self.obj = template.Variable(obj)
        self.context_var = context_var
        self.checker = template.Variable(checker) if checker else None

    def render(self, context):
        for_whom = self.for_whom.resolve(context)
        if isinstance(for_whom, get_user_model()):
            self.user = for_whom
            self.group = None
        elif isinstance(for_whom, AnonymousUser):
            self.user = get_user_model().get_anonymous()
            self.group = None
        elif isinstance(for_whom, Group):
            self.user = None
            self.group = for_whom
        else:
            raise NotUserNorGroup("User or Group instance required (got %s)"
                                  % for_whom.__class__)
        obj = self.obj.resolve(context)
        if not obj:
            return ''

        check = self.checker.resolve(context) if self.checker else ObjectPermissionChecker(for_whom)
        perms = check.get_perms(obj)

        context[self.context_var] = perms
        return ''


@register.tag
def get_obj_perms(parser, token):
    """
    Returns a list of permissions (as ``codename`` strings) for a given
    ``user``/``group`` and ``obj`` (Model instance).

    Parses ``get_obj_perms`` tag which should be in format::

        {% get_obj_perms user/group for obj as "context_var" %}

    .. note::
       Make sure that you set and use those permissions in same template
       block (``{% block %}``).

    Example of usage (assuming ``flatpage`` and ``perm`` objects are
    available from *context*)::

        {% get_obj_perms request.user for flatpage as "flatpage_perms" %}

        {% if "delete_flatpage" in flatpage_perms %}
            <a href="/pages/delete?target={{ flatpage.url }}">Remove page</a>
        {% endif %}

    .. note::
       Please remember that superusers would always get full list of permissions
       for a given object.

    .. versionadded:: 1.2

    As of v1.2, passing ``None`` as ``obj`` for this template tag won't rise
    obfuscated exception and would return empty permissions set instead.

    """
    bits = token.split_contents()
    format = '{% get_obj_perms user/group for obj as "context_var" perm_checker %}'
    if not (6 <= len(bits) <= 7) or bits[2] != 'for' or bits[4] != 'as':
        raise template.TemplateSyntaxError("get_obj_perms tag should be in "
                                           "format: %s" % format)

    for_whom = bits[1]
    obj = bits[3]
    context_var = bits[5]
    if context_var[0] != context_var[-1] or context_var[0] not in ('"', "'"):
        raise template.TemplateSyntaxError("get_obj_perms tag's context_var "
                                           "argument should be in quotes")
    context_var = context_var[1:-1]
    checker = bits[6] if len(bits) == 7 else None
    return ObjectPermissionsNode(for_whom, obj, context_var, checker)
