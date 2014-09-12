from rest_framework.fields import Field
from rest_framework.reverse import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import resolve, get_script_prefix, NoReverseMatch
from django.db.models.query import QuerySet
from rest_framework.compat import urlparse


class RelatedField(Field):
    def __init__(self, **kwargs):
        self.queryset = kwargs.pop('queryset', None)
        self.many = kwargs.pop('many', False)
        assert self.queryset is not None or kwargs.get('read_only', False), (
            'Relational field must provide a `queryset` argument, '
            'or set read_only=`True`.'
        )
        super(RelatedField, self).__init__(**kwargs)

    def get_queryset(self):
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated whenever used.
            queryset = queryset.all()
        return queryset


class StringRelatedField(Field):
    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super(StringRelatedField, self).__init__(**kwargs)

    def to_representation(self, value):
        return str(value)


class PrimaryKeyRelatedField(RelatedField):
    MESSAGES = {
        'required': 'This field is required.',
        'does_not_exist': "Invalid pk '{pk_value}' - object does not exist.",
        'incorrect_type': 'Incorrect type.  Expected pk value, received {data_type}.',
    }

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(pk=data)
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
        return self.get_queryset().get(**lookup_kwargs)

    def to_internal_value(self, value):
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
        kwargs['read_only'] = True
        kwargs['source'] = '*'
        self.view_name = kwargs.pop('view_name')
        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.lookup_url_kwarg = kwargs.pop('lookup_url_kwarg', self.lookup_field)
        super(HyperlinkedIdentityField, self).__init__(**kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if obj.pk is None:
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}
        return reverse(view_name, kwargs=kwargs, request=request, format=format)

    def to_representation(self, value):
        request = self.context.get('request', None)
        format = self.context.get('format', None)

        assert request is not None, (
            "`HyperlinkedIdentityField` requires the request in the serializer"
            " context. Add `context={'request': request}` when instantiating "
            "the serializer."
        )

        # By default use whatever format is given for the current context
        # unless the target is a different type to the source.
        #
        # Eg. Consider a HyperlinkedIdentityField pointing from a json
        # representation to an html property of that representation...
        #
        # '/snippets/1/' should link to '/snippets/1/highlight/'
        # ...but...
        # '/snippets/1/.json' should link to '/snippets/1/highlight/.html'
        if format and self.format and self.format != format:
            format = self.format

        # Return the hyperlink, or error if incorrectly configured.
        try:
            return self.get_url(value, self.view_name, request, format)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise Exception(msg % self.view_name)


class SlugRelatedField(RelatedField):
    def __init__(self, **kwargs):
        self.slug_field = kwargs.pop('slug_field', None)
