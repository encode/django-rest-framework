from django import forms
from django.core.urlresolvers import reverse, get_urlconf, get_resolver, NoReverseMatch
from django.db import models
from django.core.exceptions import ImproperlyConfigured

from djangorestframework.response import ErrorResponse
from djangorestframework.serializer import Serializer, _SkipField


class BaseResource(object):
    """
    Base class for all Resource classes, which simply defines the interface
    they provide.
    """
    fields = ()
    include = ()
    exclude = ()

    # TODO: Inheritance, like for models
    class DoesNotExist(Exception): pass

    # !!! `view` should be first kwarg to avoid backward incompatibilities. (lol)
    def __init__(self, view=None, instance=None, depth=None, stack=[], **kwargs):
        super(BaseResource, self).__init__(depth, stack, **kwargs)
        self.view = view
        self.instance = instance

    def deserialize(self, data, files=None):
        """
        Given the request content return the cleaned, validated content.
        Typically raises a :exc:`response.ErrorResponse` with status code 400
        (Bad Request) on failure.
        """
        raise NotImplementedError()

    def retrieve(self, *args, **kwargs):
        raise NotImplementedError()

    def create(self, *args, **kwargs):
        raise NotImplementedError()

    def update(self, data, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, *args, **kwargs):
        raise NotImplementedError()

    def get_url(self):
        raise NotImplementedError()

    def is_bound(self):
        return not self.instance is None


class Resource(Serializer, BaseResource):
    """
    A Resource determines how a python object maps to some serializable data.
    Objects that a resource can act on include plain Python object instances,
    Django Models, and Django QuerySets.
    """

    # The model attribute refers to the Django Model which this Resource maps
    # to. (The Model's class, rather than an instance of the Model)
    model = None

    # By default the set of returned fields will be the set of:
    #
    # 0. All the fields on the model, excluding 'id'.
    # 1. All the properties on the model.
    # 2. The absolute_url of the model, if a get_absolute_url method exists for
    #    the model.
    #
    # If you wish to override this behaviour,
    # you should explicitly set the fields attribute on your class.
    fields = None

    def deserialize(self, data, files=None):
        return data


class FormResource(Resource):
    """
    Resource class that uses forms for validation.
    Also provides a :meth:`get_bound_form` method which may be used by some
    renderers.

    On calling :meth:`deserialize` this validator may set a
    :attr:`bound_form_instance` attribute on the view, which may be used by
    some renderers.
    """

    form = None
    """
    The :class:`Form` class that should be used for request validation.
    This can be overridden by a :attr:`form` attribute on the
    :class:`views.View`.
    """

    def deserialize(self, data, files=None):
        """
        Given some content as input return some cleaned, validated content.

        Raises a :exc:`response.ErrorResponse` with status code 400
        # (Bad Request) on failure.

        Validation is standard form validation, with an additional constraint
        that *no extra unknown fields* may be supplied.

        On failure the :exc:`response.ErrorResponse` content is a dict which
        may contain :obj:`'errors'` and :obj:`'field-errors'` keys.
        If the :obj:`'errors'` key exists it is a list of strings of non-field
        errors.
        If the :obj:`'field-errors'` key exists it is a dict of
        ``{'field name as string': ['errors as strings', ...]}``.
        """
        return self._validate(data, files)

    def _validate(self, data, files, allowed_extra_fields=(), fake_data=None):
        """
        Wrapped by validate to hide the extra flags that are used in the
        implementation.

        allowed_extra_fields is a list of fields which are not defined by the
        form, but which we still expect to see on the input.

        fake_data is a string that should be used as an extra key, as a kludge
        to force `.errors` to be populated when an empty dict is supplied in
        `data`
        """

        # We'd like nice error messages even if no content is supplied.
        # Typically if an empty dict is given to a form Django will
        # return .is_valid() == False, but .errors == {}
        #
        # To get around this case we revalidate with some fake data.
        if fake_data:
            data[fake_data] = '_fake_data'
            allowed_extra_fields = tuple(allowed_extra_fields) + ('_fake_data',)

        bound_form = self.get_bound_form(data, files)

        if bound_form is None:
            return data

        if self.view is not None:
            self.view.bound_form_instance = bound_form

        data = data and data or {}
        files = files and files or {}

        seen_fields_set = set(data.keys())
        form_fields_set = set(bound_form.fields.keys())
        allowed_extra_fields_set = set(allowed_extra_fields)

        # In addition to regular validation we also ensure no additional fields are being passed in...
        unknown_fields = seen_fields_set - (form_fields_set | allowed_extra_fields_set)
        unknown_fields = unknown_fields - set(('csrfmiddlewaretoken', '_accept', '_method')) # TODO: Ugh.

        # Check using both regular validation, and our stricter no additional fields rule
        if bound_form.is_valid() and not unknown_fields:
            # Validation succeeded...
            cleaned_data = bound_form.cleaned_data

            # Add in any extra fields to the cleaned content...
            for key in (allowed_extra_fields_set & seen_fields_set) - set(cleaned_data.keys()):
                cleaned_data[key] = data[key]

            return cleaned_data

        # Validation failed...
        detail = {}

        if not bound_form.errors and not unknown_fields:
            # is_valid() was False, but errors was empty.
            # If we havn't already done so attempt revalidation with some fake data
            # to force django to give us an errors dict.
            if fake_data is None:
                return self._validate(data, files, allowed_extra_fields, '_fake_data')

            # If we've already set fake_dict and we're still here, fallback gracefully.
            detail = {u'errors': [u'No content was supplied.']}

        else:
            # Add any non-field errors
            if bound_form.non_field_errors():
                detail[u'errors'] = bound_form.non_field_errors()

            # Add standard field errors
            field_errors = dict(
                (key, map(unicode, val))
                for (key, val)
                in bound_form.errors.iteritems()
                if not key.startswith('__')
            )

            # Add any unknown field errors
            for key in unknown_fields:
                field_errors[key] = [u'This field does not exist.']

            if field_errors:
                detail[u'field_errors'] = field_errors

        # Return HTTP 400 response (BAD REQUEST)
        raise ErrorResponse(400, detail)

    def get_form_class(self, method=None):
        """
        Returns the form class used to validate this resource.
        """
        # A form on the view overrides a form on the resource.
        form = getattr(self.view, 'form', None) or self.form

        # Use the requested method or determine the request method
        if method is None and hasattr(self.view, 'request') and hasattr(self.view, 'method'):
            method = self.view.method
        elif method is None and hasattr(self.view, 'request'):
            method = self.view.request.method

        # A method form on the view or resource overrides the general case.
        # Method forms are attributes like `get_form` `post_form` `put_form`.
        if method:
            form = getattr(self, '%s_form' % method.lower(), form)
            form = getattr(self.view, '%s_form' % method.lower(), form)

        return form

    def get_bound_form(self, data=None, files=None, method=None):
        """
        Given some content return a Django form bound to that content.
        If form validation is turned off (:attr:`form` class attribute is :const:`None`) then returns :const:`None`.
        """
        form = self.get_form_class(method)

        if not form:
            return None

        if data is not None or files is not None:
            return form(data, files)

        return form()


#class _RegisterModelResource(type):
#    """
#    Auto register new ModelResource classes into ``_model_to_resource``
#    """
#    def __new__(cls, name, bases, dct):
#        resource_cls = type.__new__(cls, name, bases, dct)
#        model_cls = dct.get('model', None)
#        if model_cls:
#            _model_to_resource[model_cls] = resource_cls
#        return resource_cls


class ModelResource(FormResource):
    """
    Resource class that uses forms for validation and otherwise falls back to a
    model form if no form is set.
    Also provides a :meth:`get_bound_form` method which may be used by some
    renderers.
    """

    # Auto-register new ModelResource classes into _model_to_resource
    #__metaclass__ = _RegisterModelResource

    form = None
    """
    The form class that should be used for request validation.
    If set to :const:`None` then the default model form validation will be used.

    This can be overridden by a :attr:`form` attribute on the
    :class:`views.View`.
    """

    model = None
    """
    The model class which this resource maps to.

    This can be overridden by a :attr:`model` attribute on the
    :class:`views.View`.
    """

    fields = None
    """
    The list of fields to use on the output.

    May be any of:

    The name of a model field. To view nested resources, give the field as a
    tuple of ("fieldName", resource) where `resource` may be any of
    ModelResource reference, the name of a ModelResourc reference as a string
    or a tuple of strings representing fields on the nested model.
    The name of an attribute on the model.
    The name of an attribute on the resource.
    The name of a method on the model, with a signature like ``func(self)``.
    The name of a method on the resource, with a signature like
    ``func(self, instance)``.
    """

    exclude = ('id', 'pk')
    """
    The list of fields to exclude.  This is only used if :attr:`fields` is not
    set.
    """

    include = ('url',)
    """
    The list of extra fields to include.  This is only used if :attr:`fields`
    is not set.
    """

    def __init__(self, view=None, instance=None, depth=None, stack=[], **kwargs):
        """
        Allow :attr:`form` and :attr:`model` attributes set on the
        :class:`View` to override the :attr:`form` and :attr:`model`
        attributes set on the :class:`Resource`.
        """
        super(ModelResource, self).__init__(view=None, instance=instance, depth=depth, stack=stack, **kwargs)

        self.model = getattr(view, 'model', None) or self.model

    def retrieve(self, *args, **kwargs):
        """
        Return a model instance or None.
        """
        model = self.get_model()
        queryset = self.get_queryset()
        kwargs = self._clean_url_kwargs(kwargs)

        try:
            instance = queryset.get(**kwargs)
        except model.DoesNotExist:
            raise self.DoesNotExist
        self.instance = instance
        return self.instance

    def create(self, *args, **kwargs):
        model = self.get_model()
        kwargs = self._clean_url_kwargs(kwargs)

        self.instance = model(**kwargs)
        self.instance.save()
        return self.instance

    def update(self, data, *args, **kwargs):
        # The resource needs to be bound to an
        # instance, or updating is not possible
        if not self.is_bound():
            raise Exception("resource needs to be bound") #TODO: what exception?

        model = self.get_model()
        kwargs = self._clean_url_kwargs(kwargs)
        data = dict(data, **kwargs)

        # Updating many to many relationships
        # TODO: code very hard to understand
        m2m_data = {}
        for field in model._meta.many_to_many:
            if field.name in data:
                m2m_data[field.name] = (
                    field.m2m_reverse_field_name(), data[field.name]
                )
                del data[field.name]

        for fieldname in m2m_data:
            manager = getattr(self.instance, fieldname)

            if hasattr(manager, 'add'):
                manager.add(*m2m_data[fieldname][1])
            else:
                rdata = {}
                rdata[manager.source_field_name] = self.instance

                for related_item in m2m_data[fieldname][1]:
                    rdata[m2m_data[fieldname][0]] = related_item
                    manager.through(**rdata).save()

        # Updating other fields
        for (key, val) in data.items():
            setattr(self.instance, key, val)
        self.instance.save()
        return self.instance

    def delete(self, *args, **kwargs):
        # The resource needs to be bound to an
        # instance, or deleting is not possible
        if not self.is_bound():
            raise Exception("resource needs to be bound") #TODO: what exception?

        self.instance.delete()
        return self.instance

    def list(self, *args, **kwargs):
        # TODO: QuerysetResource instead !?
        kwargs = self._clean_url_kwargs(kwargs)
        queryset = self.get_queryset()
        ordering = self.get_ordering()

        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset.filter(**kwargs)

    def get_url(self):
        """
        Attempts to reverse resolve the url of the given model *instance* for
        this resource.

        Requires a ``View`` with :class:`mixins.InstanceMixin` to have been
        created for this resource.

        This method can be overridden if you need to set the resource url
        reversing explicitly.
        """
        # The resource needs to be bound to an
        # instance, or getting url is not possible
        if not self.is_bound():
            raise Exception("resource needs to be bound") #TODO: what exception?

        if not hasattr(self, 'view_callable'):
            raise _SkipField

        # dis does teh magicks...
        urlconf = get_urlconf()
        resolver = get_resolver(urlconf)

        possibilities = resolver.reverse_dict.getlist(self.view_callable[0])
        for tuple_item in possibilities:
            possibility = tuple_item[0]
            # pattern = tuple_item[1]
            # Note: defaults = tuple_item[2] for django >= 1.3
            for result, params in possibility:

                # instance_attrs = dict([ (param, getattr(instance, param))
                #                         for param in params
                #                         if hasattr(instance, param) ])

                instance_attrs = {}
                for param in params:
                    if not hasattr(self.instance, param):
                        continue
                    attr = getattr(self.instance, param)
                    if isinstance(attr, models.Model):
                        instance_attrs[param] = attr.pk
                    else:
                        instance_attrs[param] = attr

                try:
                    return reverse(self.view_callable[0], kwargs=instance_attrs)
                except NoReverseMatch:
                    pass
        raise _SkipField

    def deserialize(self, data, files=None):
        """
        Given some content as input return some cleaned, validated content.

        Raises a :exc:`response.ErrorResponse` with status code 400
        (Bad Request) on failure.

        Validation is standard form or model form validation,
        with an additional constraint that no extra unknown fields may be
        supplied, and that all fields specified by the fields class attribute
        must be supplied, even if they are not validated by the Form/ModelForm.

        On failure the ErrorResponse content is a dict which may contain
        :obj:`'errors'` and :obj:`'field-errors'` keys.
        If the :obj:`'errors'` key exists it is a list of strings of non-field
        errors.
        If the ''field-errors'` key exists it is a dict of
        `{field name as string: list of errors as strings}`.
        """
        return self._validate(data, files,
                              allowed_extra_fields=self._property_fields_set())

    def get_bound_form(self, data=None, files=None, method=None):
        """
        Given some content return a ``Form`` instance bound to that content.

        If the :attr:`form` class attribute has been explicitly set then that
        class will be used
        to create the Form, otherwise the model will be used to create a
        ModelForm.
        """
        form = self.get_form_class(method)

        if not form and self.model:
            # Fall back to ModelForm which we create on the fly
            class OnTheFlyModelForm(forms.ModelForm):
                class Meta:
                    model = self.model
                    #fields = tuple(self._model_fields_set)

            form = OnTheFlyModelForm

        # Both form and model not set?  Okay bruv, whatevs...
        if not form:
            return None

        # Instantiate the ModelForm as appropriate
        if data is not None or files is not None:
            if issubclass(form, forms.ModelForm) and hasattr(self.view, 'model_instance'):
                # Bound to an existing model instance
                return form(data, files, instance=self.view.model_instance)
            else:
                return form(data, files)

        return form()

    @property
    def _model_fields_set(self):
        """
        Return a set containing the names of validated fields on the model.
        """
        model_fields = set(field.name for field in self.model._meta.fields)

        if self.fields:
            return model_fields & set(self.fields)

        return model_fields - set(as_tuple(self.exclude))

    def _property_fields_set(self):
        """
        Returns a set containing the names of validated properties on the model.
        """
        property_fields = set(attr for attr in dir(self.model) if
                              isinstance(getattr(self.model, attr, None), property)
                              and not attr.startswith('_'))

        if self.fields:
            return property_fields & set(self.fields)

        return property_fields.union(set(self.include)) - set(self.exclude)

    def get_model(self):
        """
        Return the model class for this resource.
        """
        model = getattr(self, 'model', None)
        if model is None:
            model = getattr(self.view, 'model', None)
            if model is None:
                raise ImproperlyConfigured(u"%(cls)s is missing a model. Define "
                                           u"%(cls)s.model." % {
                                                'cls': self.__class__
                                           })
        return model

    def get_queryset(self):
        """
        Return the queryset that should be used when retrieving or listing
        instances.
        """
        queryset = getattr(self, 'queryset', None)
        if queryset is None:
            queryset = getattr(self.view, 'queryset', None)
            if queryset is None:
                try:
                    model = self.get_model()
                except ImproperlyConfigured:
                    raise ImproperlyConfigured(u"%(cls)s is missing a queryset. Define "
                                               u"%(cls)s.model or %(cls)s.queryset." % {
                                                    'cls': self.__class__
                                               })
                queryset = model._default_manager.all()
        return queryset._clone()

    def get_ordering(self):
        """
        Return the ordering that should be used when listing instances.
        """
        return getattr(self, 'ordering',
                    getattr(self.view, 'ordering',
                        None))

    def _clean_url_kwargs(self, kwargs):
        # TODO: probably this functionality shouldn't be there
        from djangorestframework.renderers import BaseRenderer
        format_arg = BaseRenderer._FORMAT_QUERY_PARAM
        if format_arg in kwargs:
            kwargs = kwargs.copy()
            del kwargs[format_arg]
        return kwargs
