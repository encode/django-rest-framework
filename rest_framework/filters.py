"""
Provides generic filtering backends that can be used to filter the results
returned by list views.
"""
import operator
import warnings
from functools import reduce

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.template import loader
from django.utils.encoding import force_str
from django.utils.text import smart_split, unescape_string_literal
from django.utils.translation import gettext_lazy as _

from rest_framework import RemovedInDRF317Warning
from rest_framework.compat import coreapi, coreschema
from rest_framework.fields import CharField
from rest_framework.settings import api_settings


def search_smart_split(search_terms):
    """generator that first splits string by spaces, leaving quoted phrases together,
    then it splits non-quoted phrases by commas.
    """
    split_terms = []
    for term in smart_split(search_terms):
        # trim commas to avoid bad matching for quoted phrases
        term = term.strip(',')
        if term.startswith(('"', "'")) and term[0] == term[-1]:
            # quoted phrases are kept together without any other split
            split_terms.append(unescape_string_literal(term))
        else:
            # non-quoted tokens are split by comma, keeping only non-empty ones
            for sub_term in term.split(','):
                if sub_term:
                    split_terms.append(sub_term.strip())
    return split_terms


class BaseFilterBackend:
    """
    A base class from which all filter backend classes should inherit.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        raise NotImplementedError(".filter_queryset() must be overridden.")

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        if coreapi is not None:
            warnings.warn('CoreAPI compatibility is deprecated and will be removed in DRF 3.17', RemovedInDRF317Warning)
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return []

    def get_schema_operation_parameters(self, view):
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
    search_title = _('Search')
    search_description = _('A search term.')

    def get_search_fields(self, view, request):
        """
        Search fields are obtained from the view, but the request is always
        passed to this method. Sub-classes can override this method to
        dynamically change the search fields based on request content.
        """
        return getattr(view, 'search_fields', None)

    def get_search_terms(self, request):
        """
        Search terms are set by a ?search=... query parameter,
        and may be whitespace delimited.
        """
        value = request.query_params.get(self.search_param, '')
        field = CharField(trim_whitespace=False, allow_blank=True)
        cleaned_value = field.run_validation(value)
        return search_smart_split(cleaned_value)

    def construct_search(self, field_name, queryset):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            # Use field_name if it includes a lookup.
            opts = queryset.model._meta
            lookup_fields = field_name.split(LOOKUP_SEP)
            # Go through the fields, following all relations.
            prev_field = None
            for path_part in lookup_fields:
                if path_part == "pk":
                    path_part = opts.pk.name
                try:
                    field = opts.get_field(path_part)
                except FieldDoesNotExist:
                    # Use valid query lookups.
                    if prev_field and prev_field.get_lookup(path_part):
                        return field_name
                else:
                    prev_field = field
                    if hasattr(field, "path_infos"):
                        # Update opts to follow the relation.
                        opts = field.path_infos[-1].to_opts
                    # django < 4.1
                    elif hasattr(field, 'get_path_info'):
                        # Update opts to follow the relation.
                        opts = field.get_path_info()[-1].to_opts
            # Otherwise, use the field with icontains.
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
            # Annotated fields do not need to be distinct
            if isinstance(queryset, models.QuerySet) and search_field in queryset.query.annotations:
                continue
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
                else:
                    # This field has a custom __ query transform but is not a relational field.
                    break
        return False

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field), queryset)
            for search_field in search_fields
        ]

        base = queryset
        # generator which for each term builds the corresponding search
        conditions = (
            reduce(
                operator.or_,
                (models.Q(**{orm_lookup: term}) for orm_lookup in orm_lookups)
            ) for term in search_terms
        )
        queryset = queryset.filter(reduce(operator.and_, conditions))

        # Remove duplicates from results, if necessary
        if self.must_call_distinct(queryset, search_fields):
            # inspired by django.contrib.admin
            # this is more accurate than .distinct form M2M relationship
            # also is cross-database
            queryset = queryset.filter(pk=models.OuterRef('pk'))
            queryset = base.filter(models.Exists(queryset))
        return queryset

    def to_html(self, request, queryset, view):
        if not getattr(view, 'search_fields', None):
            return ''

        context = {
            'param': self.search_param,
            'term': request.query_params.get(self.search_param, ''),
        }
        template = loader.get_template(self.template)
        return template.render(context)

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        if coreapi is not None:
            warnings.warn('CoreAPI compatibility is deprecated and will be removed in DRF 3.17', RemovedInDRF317Warning)
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.search_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_str(self.search_title),
                    description=force_str(self.search_description)
                )
            )
        ]

    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.search_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.search_description),
                'schema': {
                    'type': 'string',
                },
            },
        ]


class OrderingFilter(BaseFilterBackend):
    # The URL query parameter used for the ordering.
    ordering_param = api_settings.ORDERING_PARAM
    ordering_fields = None
    ordering_title = _('Ordering')
    ordering_description = _('Which field to use when ordering the results.')
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
        if isinstance(ordering, str):
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

        model_class = queryset.model
        model_property_names = [
            # 'pk' is a property added in Django's Model class, however it is valid for ordering.
            attr for attr in dir(model_class) if isinstance(getattr(model_class, attr), property) and attr != 'pk'
        ]

        return [
            (field.source.replace('.', '__') or field_name, field.label)
            for field_name, field in serializer_class(context=context).fields.items()
            if (
                not getattr(field, 'write_only', False) and
                not field.source == '*' and
                field.source not in model_property_names
            )
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
                for key in queryset.query.annotations
            ]
        else:
            valid_fields = [
                (item, item) if isinstance(item, str) else item
                for item in valid_fields
            ]

        return valid_fields

    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = [item[0] for item in self.get_valid_fields(queryset, view, {'request': request})]

        def term_valid(term):
            if term.startswith("-"):
                term = term[1:]
            return term in valid_fields

        return [term for term in fields if term_valid(term)]

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            return queryset.order_by(*ordering)

        return queryset

    def get_template_context(self, request, queryset, view):
        current = self.get_ordering(request, queryset, view)
        current = None if not current else current[0]
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
        return template.render(context)

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        if coreapi is not None:
            warnings.warn('CoreAPI compatibility is deprecated and will be removed in DRF 3.17', RemovedInDRF317Warning)
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.ordering_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_str(self.ordering_title),
                    description=force_str(self.ordering_description)
                )
            )
        ]

    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.ordering_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.ordering_description),
                'schema': {
                    'type': 'string',
                },
            },
        ]
