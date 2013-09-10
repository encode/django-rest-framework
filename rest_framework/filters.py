"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""
from __future__ import unicode_literals
from django.db import models
from rest_framework.compat import django_filters, six, guardian
from functools import reduce
import operator

FilterSet = django_filters and django_filters.FilterSet or None


class BaseFilterBackend(object):
    """
    A base class from which all filter backend classes should inherit.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        raise NotImplementedError(".filter_queryset() must be overridden.")


class DjangoFilterBackend(BaseFilterBackend):
    """
    A filter backend that uses django-filter.
    """
    default_filter_set = FilterSet

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

            assert issubclass(filter_model, queryset.model), \
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
            return filter_class(request.QUERY_PARAMS, queryset=queryset).qs

        return queryset


class SearchFilter(BaseFilterBackend):
    search_param = 'search'  # The URL query parameter used for the search.

    def get_search_terms(self, request):
        """
        Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited.
        """
        params = request.QUERY_PARAMS.get(self.search_param, '')
        return params.replace(',', ' ').split()

    def construct_search(self, field_name):
        if field_name.startswith('^'):
            return "%s__istartswith" % field_name[1:]
        elif field_name.startswith('='):
            return "%s__iexact" % field_name[1:]
        elif field_name.startswith('@'):
            return "%s__search" % field_name[1:]
        else:
            return "%s__icontains" % field_name

    def filter_queryset(self, request, queryset, view):
        search_fields = getattr(view, 'search_fields', None)

        if not search_fields:
            return queryset

        orm_lookups = [self.construct_search(str(search_field))
                       for search_field in search_fields]

        for search_term in self.get_search_terms(request):
            or_queries = [models.Q(**{orm_lookup: search_term})
                          for orm_lookup in orm_lookups]
            queryset = queryset.filter(reduce(operator.or_, or_queries))

        return queryset


class OrderingFilter(BaseFilterBackend):
    ordering_param = 'ordering'  # The URL query parameter used for the ordering.

    def get_ordering(self, request):
        """
        Ordering is set by a comma delimited ?ordering=... query parameter.
        """
        params = request.QUERY_PARAMS.get(self.ordering_param)
        if params:
            return [param.strip() for param in params.split(',')]

    def get_default_ordering(self, view):
        ordering = getattr(view, 'ordering', None)
        if isinstance(ordering, six.string_types):
            return (ordering,)
        return ordering

    def remove_invalid_fields(self, queryset, ordering):
        field_names = [field.name for field in queryset.model._meta.fields]
        return [term for term in ordering if term.lstrip('-') in field_names]

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request)

        if ordering:
            # Skip any incorrect parameters
            ordering = self.remove_invalid_fields(queryset, ordering)

        if not ordering:
            # Use 'ordering' attribute by default
            ordering = self.get_default_ordering(view)

        if ordering:
            return queryset.order_by(*ordering)

        return queryset


class DjangoObjectPermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    def __init__(self):
        assert guardian, 'Using DjangoObjectPermissionsFilter, but django-guardian is not installed'

    perm_format = '%(app_label)s.view_%(model_name)s'

    def filter_queryset(self, request, queryset, view):
        user = request.user
        model_cls = queryset.model
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.module_name
        }
        permission = self.perm_format % kwargs
        return guardian.shortcuts.get_objects_for_user(user, permission, queryset)
