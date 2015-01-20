# coding: utf-8
from __future__ import unicode_literals
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.core.urlresolvers import resolve, get_script_prefix, NoReverseMatch, Resolver404
from django.db.models.query import QuerySet
from django.utils import six
from django.utils.encoding import smart_text
from django.utils.six.moves.urllib import parse as urlparse
from django.utils.translation import ugettext_lazy as _
from rest_framework.compat import OrderedDict
from rest_framework.fields import get_attribute, empty, Field
from rest_framework.reverse import reverse
from rest_framework.utils import html


class PKOnlyObject(object):
    """
    This is a mock object, used for when we only need the pk of the object
    instance, but still want to return an object with a .pk attribute,
    in order to keep the same interface as a regular model instance.
    """
    def __init__(self, pk):
        self.pk = pk


# We assume that 'validators' are intended for the child serializer,
# rather than the parent serializer.
MANY_RELATION_KWARGS = (
    'read_only', 'write_only', 'required', 'default', 'initial', 'source',
    'label', 'help_text', 'style', 'error_messages'
)


class RelatedField(Field):
    def __init__(self, **kwargs):
        self.queryset = kwargs.pop('queryset', None)
        assert self.queryset is not None or kwargs.get('read_only', None), (
            'Relational field must provide a `queryset` argument, '
            'or set read_only=`True`.'
        )
        assert not (self.queryset is not None and kwargs.get('read_only', None)), (
            'Relational fields should not provide a `queryset` argument, '
            'when setting read_only=`True`.'
        )
        super(RelatedField, self).__init__(**kwargs)

    def __new__(cls, *args, **kwargs):
        # We override this method in order to automagically create
        # `ManyRelatedField` classes instead when `many=True` is set.
        if kwargs.pop('many', False):
            return cls.many_init(*args, **kwargs)
        return super(RelatedField, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        This method handles creating a parent `ManyRelatedField` instance
        when the `many=True` keyword argument is passed.

        Typically you won't need to override this method.

        Note that we're over-cautious in passing most arguments to both parent
        and child classes in order to try to cover the general case. If you're
        overriding this method you'll probably want something much simpler, eg:

        @classmethod
        def many_init(cls, *args, **kwargs):
            kwargs['child'] = cls()
            return CustomManyRelatedField(*args, **kwargs)
        """
        list_kwargs = {'child_relation': cls(*args, **kwargs)}
        for key in kwargs.keys():
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return ManyRelatedField(**list_kwargs)

    def run_validation(self, data=empty):
        # We force empty strings to None values for relational fields.
        if data == '':
            data = None
        return super(RelatedField, self).run_validation(data)

    def get_queryset(self):
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated whenever used.
            queryset = queryset.all()
        return queryset

    def use_pk_only_optimization(self):
        return False

    def get_attribute(self, instance):
        if self.use_pk_only_optimization() and self.source_attrs:
            # Optimized case, return a mock object only containing the pk attribute.
            try:
                instance = get_attribute(instance, self.source_attrs[:-1])
                return PKOnlyObject(pk=instance.serializable_value(self.source_attrs[-1]))
            except AttributeError:
                pass

        # Standard case, return the object instance.
        return get_attribute(instance, self.source_attrs)

    @property
    def choices(self):
        return OrderedDict([
            (
                six.text_type(self.to_representation(item)),
                six.text_type(item)
            )
            for item in self.queryset.all()
        ])


class StringRelatedField(RelatedField):
    """
    A read only field that represents its targets using their
    plain string representation.
    """

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super(StringRelatedField, self).__init__(**kwargs)

    def to_representation(self, value):
        return six.text_type(value)


class PrimaryKeyRelatedField(RelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _("Invalid pk '{pk_value}' - object does not exist."),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def use_pk_only_optimization(self):
        return True

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        return value.pk


class HyperlinkedRelatedField(RelatedField):
    lookup_field = 'pk'

    default_error_messages = {
        'required': _('This field is required.'),
        'no_match': _('Invalid hyperlink - No URL match'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match.'),
        'does_not_exist': _('Invalid hyperlink - Object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected URL string, received {data_type}.'),
    }

    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        self.view_name = view_name
        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.lookup_url_kwarg = kwargs.pop('lookup_url_kwarg', self.lookup_field)
        self.format = kwargs.pop('format', None)

        # We include these simply for dependency injection in tests.
        # We can't add them as class attributes or they would expect an
        # implicit `self` argument to be passed.
        self.reverse = reverse
        self.resolve = resolve

        super(HyperlinkedRelatedField, self).__init__(**kwargs)

    def use_pk_only_optimization(self):
        return self.lookup_field == 'pk'

    def get_object(self, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and should return an
        object instance, or raise an `ObjectDoesNotExist` exception.
        """
        lookup_value = view_kwargs[self.lookup_url_kwarg]
        lookup_kwargs = {self.lookup_field: lookup_value}
        return self.get_queryset().get(**lookup_kwargs)

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
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)

    def to_internal_value(self, data):
        try:
            http_prefix = data.startswith(('http:', 'https:'))
        except AttributeError:
            self.fail('incorrect_type', data_type=type(data).__name__)

        if http_prefix:
            # If needed convert absolute URLs to relative path
            data = urlparse.urlparse(data).path
            prefix = get_script_prefix()
            if data.startswith(prefix):
                data = '/' + data[len(prefix):]

        try:
            match = self.resolve(data)
        except Resolver404:
            self.fail('no_match')

        if match.view_name != self.view_name:
            self.fail('incorrect_match')

        try:
            return self.get_object(match.view_name, match.args, match.kwargs)
        except (ObjectDoesNotExist, TypeError, ValueError):
            self.fail('does_not_exist')

    def to_representation(self, value):
        request = self.context.get('request', None)
        format = self.context.get('format', None)

        assert request is not None, (
            "`%s` requires the request in the serializer"
            " context. Add `context={'request': request}` when instantiating "
            "the serializer." % self.__class__.__name__
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
            raise ImproperlyConfigured(msg % self.view_name)


class HyperlinkedIdentityField(HyperlinkedRelatedField):
    """
    A read-only field that represents the identity URL for an object, itself.

    This is in contrast to `HyperlinkedRelatedField` which represents the
    URL of relationships to other objects.
    """

    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        kwargs['read_only'] = True
        kwargs['source'] = '*'
        super(HyperlinkedIdentityField, self).__init__(view_name, **kwargs)

    def use_pk_only_optimization(self):
        # We have the complete object instance already. We don't need
        # to run the 'only get the pk for this relationship' code.
        return False


class SlugRelatedField(RelatedField):
    """
    A read-write field the represents the target of the relationship
    by a unique 'slug' attribute.
    """

    default_error_messages = {
        'does_not_exist': _("Object with {slug_name}={value} does not exist."),
        'invalid': _('Invalid value.'),
    }

    def __init__(self, slug_field=None, **kwargs):
        assert slug_field is not None, 'The `slug_field` argument is required.'
        self.slug_field = slug_field
        super(SlugRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return getattr(obj, self.slug_field)


class ManyRelatedField(Field):
    """
    Relationships with `many=True` transparently get coerced into instead being
    a ManyRelatedField with a child relationship.

    The `ManyRelatedField` class is responsible for handling iterating through
    the values and passing each one to the child relationship.

    This class is treated as private API.
    You shouldn't generally need to be using this class directly yourself,
    and should instead simply set 'many=True' on the relationship.
    """
    initial = []
    default_empty_html = []

    def __init__(self, child_relation=None, *args, **kwargs):
        self.child_relation = child_relation
        assert child_relation is not None, '`child_relation` is a required argument.'
        super(ManyRelatedField, self).__init__(*args, **kwargs)
        self.child_relation.bind(field_name='', parent=self)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if html.is_html_input(dictionary):
            return dictionary.getlist(self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_internal_value(self, data):
        return [
            self.child_relation.to_internal_value(item)
            for item in data
        ]

    def get_attribute(self, instance):
        relationship = get_attribute(instance, self.source_attrs)
        return relationship.all() if (hasattr(relationship, 'all')) else relationship

    def to_representation(self, iterable):
        return [
            self.child_relation.to_representation(value)
            for value in iterable
        ]

    @property
    def choices(self):
        queryset = self.child_relation.queryset
        iterable = queryset.all() if (hasattr(queryset, 'all')) else queryset
        items_and_representations = [
            (item, self.child_relation.to_representation(item))
            for item in iterable
        ]
        return OrderedDict([
            (
                six.text_type(item_representation),
                six.text_type(item) + ' - ' + six.text_type(item_representation)
            )
            for item, item_representation in items_and_representations
        ])
