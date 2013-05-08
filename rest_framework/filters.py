"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""
from __future__ import unicode_literals

from django.db import models
from rest_framework.compat import django_filters
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

    def get_filter_class(self, view):
        """
        Return the django-filters `FilterSet` used to filter the queryset.
        """
        filter_class = getattr(view, 'filter_class', None)
        filter_fields = getattr(view, 'filter_fields', None)
        model_cls = getattr(view, 'model', None)
        queryset = getattr(view, 'queryset', None)
        if model_cls is None and queryset is not None:
            model_cls = queryset.model

        if filter_class:
            filter_model = filter_class.Meta.model

            assert issubclass(filter_model, model_cls), \
                'FilterSet model %s does not match view model %s' % \
                (filter_model, model_cls)

            return filter_class

        if filter_fields:
            assert model_cls is not None, 'Cannot use DjangoFilterBackend ' \
                'on a view which does not have a .model or .queryset attribute.'

            class AutoFilterSet(self.default_filter_set):
                class Meta:
                    model = model_cls
                    fields = filter_fields
            return AutoFilterSet

        return None

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view)

        if filter_class:
            return filter_class(request.QUERY_PARAMS, queryset=queryset).qs

        return queryset


class SearchFilter(BaseFilterBackend):
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
            return None

        orm_lookups = [self.construct_search(str(search_field))
                       for search_field in self.search_fields]
        for bit in self.query.split():
            or_queries = [models.Q(**{orm_lookup: bit})
                          for orm_lookup in orm_lookups]
            queryset = queryset.filter(reduce(operator.or_, or_queries))
        return queryset
