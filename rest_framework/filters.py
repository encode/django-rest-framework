"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""
from __future__ import unicode_literals

import operator
from functools import reduce

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.template import loader
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from rest_framework.compat import (
    crispy_forms, distinct, django_filters, guardian, template_render
)
from rest_framework.settings import api_settings

if 'crispy_forms' in settings.INSTALLED_APPS and crispy_forms and django_filters:
    # If django-crispy-forms is installed, use it to get a bootstrap3 rendering
    # of the DjangoFilterBackend controls when displayed as HTML.
    from crispy_forms.helper import FormHelper
    from crispy_forms.layout import Layout, Submit

    class FilterSet(django_filters.FilterSet):
        def __init__(self, *args, **kwargs):
            super(FilterSet, self).__init__(*args, **kwargs)
            for field in self.form.fields.values():
                field.help_text = None

            layout_components = list(self.form.fields.keys()) + [
                Submit('', _('Submit'), css_class='btn-default'),
            ]

            helper = FormHelper()
            helper.form_method = 'GET'
            helper.template_pack = 'bootstrap3'
            helper.layout = Layout(*layout_components)

            self.form.helper = helper

    filter_template = 'rest_framework/filters/django_filter_crispyforms.html'

elif django_filters:
    # If django-crispy-forms is not installed, use the standard
    # 'form.as_p' rendering when DjangoFilterBackend is displayed as HTML.
    class FilterSet(django_filters.FilterSet):
        def __init__(self, *args, **kwargs):
            super(FilterSet, self).__init__(*args, **kwargs)
            for field in self.form.fields.values():
                field.help_text = None

    filter_template = 'rest_framework/filters/django_filter.html'

else:
    FilterSet = None
    filter_template = None


class BaseFilterBackend(object):
    """
    A base class from which all filter backend classes should inherit.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        raise NotImplementedError(".filter_queryset() must be overridden.")

    def get_fields(self, view):
        return []


class DjangoFilterBackend(BaseFilterBackend):
    """
    A filter backend that uses django-filter.
    """
    default_filter_set = FilterSet
    template = filter_template

    def __init__(self):
        assert django_filters, 'Using DjangoFilterBackend, but django-filter is not installed'

    def get_filter_class(self, view, queryset=None):
        """
        Return the django-filters `FilterSet` used to filter the queryset.
        """
        filter_class = getattr(view, 'filter_class', None)
        filter_fields = getattr(view, 'filter_fields', None)

        if filter_class:
            filter_model = filter_class.Meta.model

            assert issubclass(queryset.model, filter_model), \
                'FilterSet model %s does not match queryset model %s' % \
                (filter_model, queryset.model)

            return filter_class

        if filter_fields:
            class AutoFilterSet(self.default_filter_set):
                class Meta:
                    model = queryset.model
                    fields = filter_fields

            return AutoFilterSet

        return None

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            return filter_class(request.query_params, queryset=queryset).qs

        return queryset

    def to_html(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        if not filter_class:
            return None
        filter_instance = filter_class(request.query_params, queryset=queryset)
        context = {
            'filter': filter_instance
        }
        template = loader.get_template(self.template)
        return template_render(template, context)

    def get_fields(self, view):
        filter_class = getattr(view, 'filter_class', None)
        if filter_class:
            return list(filter_class().filters.keys())

        filter_fields = getattr(view, 'filter_fields', None)
        if filter_fields:
            return filter_fields

        return []


class SearchFilter(BaseFilterBackend):
    # The URL query parameter used for the search.
    search_param = api_settings.SEARCH_PARAM
    template = 'rest_framework/filters/search.html'
    lookup_prefixes = {
        '^': 'istartswith',
        '=': 'iexact',
        '@': 'search',
        '$': 'iregex',
    }

    def get_search_terms(self, request):
        """
        Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited.
        """
        params = request.query_params.get(self.search_param, '')
        return params.replace(',', ' ').split()

    def construct_search(self, field_name):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = 'icontains'
        return LOOKUP_SEP.join([field_name, lookup])

    def must_call_distinct(self, queryset, search_fields):
        """
        Return True if 'distinct()' should be used to query the given lookups.
        """
        for search_field in search_fields:
            opts = queryset.model._meta
            if search_field[0] in self.lookup_prefixes:
                search_field = search_field[1:]
            parts = search_field.split(LOOKUP_SEP)
            for part in parts:
                field = opts.get_field(part)
                if hasattr(field, 'get_path_info'):
                    # This field is a relation, update opts to follow the relation
                    path_info = field.get_path_info()
                    opts = path_info[-1].to_opts
                    if any(path.m2m for path in path_info):
                        # This field is a m2m relation so we know we need to call distinct
                        return True
        return False

    def filter_queryset(self, request, queryset, view):
        search_fields = getattr(view, 'search_fields', None)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(six.text_type(search_field))
            for search_field in search_fields
        ]

        base = queryset
        for search_term in search_terms:
            queries = [
                models.Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
            queryset = queryset.filter(reduce(operator.or_, queries))

        if self.must_call_distinct(queryset, search_fields):
            # Filtering against a many-to-many field requires us to
            # call queryset.distinct() in order to avoid duplicate items
            # in the resulting queryset.
            # We try to avoid this is possible, for performance reasons.
            queryset = distinct(queryset, base)
        return queryset

    def to_html(self, request, queryset, view):
        if not getattr(view, 'search_fields', None):
            return ''

        term = self.get_search_terms(request)
        term = term[0] if term else ''
        context = {
            'param': self.search_param,
            'term': term
        }
        template = loader.get_template(self.template)
        return template_render(template, context)

    def get_fields(self, view):
        return [self.search_param]


class OrderingFilter(BaseFilterBackend):
    # The URL query parameter used for the ordering.
    ordering_param = api_settings.ORDERING_PARAM
    ordering_fields = None
    template = 'rest_framework/filters/ordering.html'

    def get_ordering(self, request, queryset, view):
        """
        Ordering is set by a comma delimited ?ordering=... query parameter.

        The `ordering` query parameter can be overridden by setting
        the `ordering_param` value on the OrderingFilter or by
        specifying an `ORDERING_PARAM` value in the API settings.
        """
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = self.remove_invalid_fields(queryset, fields, view, request)
            if ordering:
                return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(view)

    def get_default_ordering(self, view):
        ordering = getattr(view, 'ordering', None)
        if isinstance(ordering, six.string_types):
            return (ordering,)
        return ordering

    def get_default_valid_fields(self, queryset, view, context={}):
        # If `ordering_fields` is not specified, then we determine a default
        # based on the serializer class, if one exists on the view.
        if hasattr(view, 'get_serializer_class'):
            try:
                serializer_class = view.get_serializer_class()
            except AssertionError:
                # Raised by the default implementation if
                # no serializer_class was found
                serializer_class = None
        else:
            serializer_class = getattr(view, 'serializer_class', None)

        if serializer_class is None:
            msg = (
                "Cannot use %s on a view which does not have either a "
                "'serializer_class', an overriding 'get_serializer_class' "
                "or 'ordering_fields' attribute."
            )
            raise ImproperlyConfigured(msg % self.__class__.__name__)

        return [
            (field.source or field_name, field.label)
            for field_name, field in serializer_class(context=context).fields.items()
            if not getattr(field, 'write_only', False) and not field.source == '*'
        ]

    def get_valid_fields(self, queryset, view, context={}):
        valid_fields = getattr(view, 'ordering_fields', self.ordering_fields)

        if valid_fields is None:
            # Default to allowing filtering on serializer fields
            return self.get_default_valid_fields(queryset, view, context)

        elif valid_fields == '__all__':
            # View explicitly allows filtering on any model field
            valid_fields = [
                (field.name, field.verbose_name) for field in queryset.model._meta.fields
            ]
            valid_fields += [
                (key, key.title().split('__'))
                for key in queryset.query.annotations.keys()
            ]
        else:
            valid_fields = [
                (item, item) if isinstance(item, six.string_types) else item
                for item in valid_fields
            ]

        return valid_fields

    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = [item[0] for item in self.get_valid_fields(queryset, view, {'request': request})]
        return [term for term in fields if term.lstrip('-') in valid_fields]

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            return queryset.order_by(*ordering)

        return queryset

    def get_template_context(self, request, queryset, view):
        current = self.get_ordering(request, queryset, view)
        current = None if current is None else current[0]
        options = []
        context = {
            'request': request,
            'current': current,
            'param': self.ordering_param,
        }
        for key, label in self.get_valid_fields(queryset, view, context):
            options.append((key, '%s - %s' % (label, _('ascending'))))
            options.append(('-' + key, '%s - %s' % (label, _('descending'))))
        context['options'] = options
        return context

    def to_html(self, request, queryset, view):
        template = loader.get_template(self.template)
        context = self.get_template_context(request, queryset, view)
        return template_render(template, context)

    def get_fields(self, view):
        return [self.ordering_param]


class DjangoObjectPermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    def __init__(self):
        assert guardian, 'Using DjangoObjectPermissionsFilter, but django-guardian is not installed'

    perm_format = '%(app_label)s.view_%(model_name)s'

    def filter_queryset(self, request, queryset, view):
        extra = {}
        user = request.user
        model_cls = queryset.model
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        permission = self.perm_format % kwargs
        if tuple(guardian.VERSION) >= (1, 3):
            # Maintain behavior compatibility with versions prior to 1.3
            extra = {'accept_global_perms': False}
        else:
            extra = {}
        return guardian.shortcuts.get_objects_for_user(user, permission, queryset, **extra)
