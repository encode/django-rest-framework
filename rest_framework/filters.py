from __future__ import unicode_literals
from rest_framework.compat import django_filters

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
        view_model = getattr(view, 'model', None)

        if filter_class:
            filter_model = filter_class.Meta.model

            assert issubclass(filter_model, view_model), \
                'FilterSet model %s does not match view model %s' % \
                (filter_model, view_model)

            return filter_class

        if filter_fields:
            class AutoFilterSet(self.default_filter_set):
                class Meta:
                    model = view_model
                    fields = filter_fields
            return AutoFilterSet

        return None

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view)

        if filter_class:
            return filter_class(request.QUERY_PARAMS, queryset=queryset).qs

        return queryset
