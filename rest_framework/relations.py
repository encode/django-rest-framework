from rest_framework.fields import Field
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import resolve, get_script_prefix
from rest_framework.compat import urlparse


def get_default_queryset(serializer_class, field_name):
    manager = getattr(serializer_class.opts.model, field_name)
    if hasattr(manager, 'related'):
        # Forward relationships
        return manager.related.model._default_manager.all()
    # Reverse relationships
    return manager.field.rel.to._default_manager.all()


class RelatedField(Field):
    def __init__(self, **kwargs):
        self.queryset = kwargs.pop('queryset', None)
        self.many = kwargs.pop('many', False)
        super(RelatedField, self).__init__(**kwargs)

    def bind(self, field_name, parent, root):
        super(RelatedField, self).bind(field_name, parent, root)
        if self.queryset is None and not self.read_only:
            self.queryset = get_default_queryset(parent, self.source)


class PrimaryKeyRelatedField(RelatedField):
    MESSAGES = {
        'required': 'This field is required.',
        'does_not_exist': "Invalid pk '{pk_value}' - object does not exist.",
        'incorrect_type': 'Incorrect type.  Expected pk value, received {data_type}.',
    }

    def from_native(self, data):
        try:
            return self.queryset.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class HyperlinkedRelatedField(RelatedField):
    lookup_field = 'pk'

    MESSAGES = {
        'required': 'This field is required.',
        'no_match': 'Invalid hyperlink - No URL match',
        'incorrect_match': 'Invalid hyperlink - Incorrect URL match.',
        'does_not_exist': "Invalid hyperlink - Object does not exist.",
        'incorrect_type': 'Incorrect type.  Expected URL string, received {data_type}.',
    }

    def __init__(self, **kwargs):
        self.view_name = kwargs.pop('view_name')
        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.lookup_url_kwarg = kwargs.pop('lookup_url_kwarg', self.lookup_field)
        super(HyperlinkedRelatedField, self).__init__(**kwargs)

    def get_object(self, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and should return an
        object instance, or raise an `ObjectDoesNotExist` exception.
        """
        lookup_value = view_kwargs[self.lookup_url_kwarg]
        lookup_kwargs = {self.lookup_field: lookup_value}
        return self.queryset.get(**lookup_kwargs)

    def from_native(self, value):
        try:
            http_prefix = value.startswith(('http:', 'https:'))
        except AttributeError:
            self.fail('incorrect_type', data_type=type(value).__name__)

        if http_prefix:
            # If needed convert absolute URLs to relative path
            value = urlparse.urlparse(value).path
            prefix = get_script_prefix()
            if value.startswith(prefix):
                value = '/' + value[len(prefix):]

        try:
            match = resolve(value)
        except Exception:
            self.fail('no_match')

        if match.view_name != self.view_name:
            self.fail('incorrect_match')

        try:
            return self.get_object(match.view_name, match.args, match.kwargs)
        except (ObjectDoesNotExist, TypeError, ValueError):
            self.fail('does_not_exist')


class HyperlinkedIdentityField(RelatedField):
    lookup_field = 'pk'

    def __init__(self, **kwargs):
        self.view_name = kwargs.pop('view_name')
        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.lookup_url_kwarg = kwargs.pop('lookup_url_kwarg', self.lookup_field)
        super(HyperlinkedIdentityField, self).__init__(**kwargs)


class SlugRelatedField(RelatedField):
    def __init__(self, **kwargs):
        self.slug_field = kwargs.pop('slug_field', None)
