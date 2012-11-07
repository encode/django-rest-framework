from rest_framework.compat import django_filters


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

    def get_filter_class(self, view):
        """
        Return the django-filters `FilterSet` used to filter the queryset.
        """
        filter_class = getattr(view, 'filter_class', None)
        filter_fields = getattr(view, 'filter_fields', None)
        filter_model = getattr(view, 'model', None)

        if filter_class or filter_fields:
            assert django_filters, 'django-filter is not installed'

        if filter_class:
            assert issubclass(filter_class.Meta.model, filter_model), \
                '%s is not a subclass of %s' % (filter_class.Meta.model, filter_model)
            return filter_class

        if filter_fields:
            class AutoFilterSet(django_filters.FilterSet):
                class Meta:
                    model = filter_model
                fields = filter_fields
            return AutoFilterSet

        return None

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view)

        if filter_class:
            return filter_class(request.GET, queryset=queryset)

        return queryset
