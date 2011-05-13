from django import forms
from django.core.urlresolvers import reverse, get_urlconf, get_resolver, NoReverseMatch
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField
from django.utils.encoding import smart_unicode

import decimal
import inspect
import re



def _model_to_dict(instance, resource=None):
    """
    Given a model instance, return a ``dict`` representing the model.
    
    The implementation is similar to Django's ``django.forms.model_to_dict``, except:

    * It doesn't coerce related objects into primary keys.
    * It doesn't drop ``editable=False`` fields.
    * It also supports attribute or method fields on the instance or resource.
    """
    opts = instance._meta
    data = {}

    #print [rel.name for rel in opts.get_all_related_objects()]
    #related = [rel.get_accessor_name() for rel in opts.get_all_related_objects()]
    #print [getattr(instance, rel) for rel in related]
    #if resource.fields:
    #    fields = resource.fields
    #else:
    #    fields = set(opts.fields + opts.many_to_many)
    
    fields = resource.fields
    include = resource.include
    exclude = resource.exclude

    extra_fields = fields and list(resource.fields) or []

    # Model fields
    for f in opts.fields + opts.many_to_many:
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, models.ForeignKey):
            data[f.name] = getattr(instance, f.name)
        else:
            data[f.name] = f.value_from_object(instance)
        
        if extra_fields and f.name in extra_fields:
            extra_fields.remove(f.name)
    
    # Method fields
    for fname in extra_fields:
        if hasattr(resource, fname):
            # check the resource first, to allow it to override fields
            obj = getattr(resource, fname)
            # if it's a method like foo(self, instance), then call it 
            if inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) == 2:
                obj = obj(instance)
        elif hasattr(instance, fname):
            # now check the object instance
            obj = getattr(instance, fname)
        else:
            continue

        # TODO: It would be nicer if this didn't recurse here.
        # Let's keep _model_to_dict flat, and _object_to_data recursive.
        data[fname] = _object_to_data(obj)
   
    return data


def _object_to_data(obj, resource=None):
    """
    Convert an object into a serializable representation.
    """
    if isinstance(obj, dict):
        # dictionaries
        # TODO: apply same _model_to_dict logic fields/exclude here
        return dict([ (key, _object_to_data(val)) for key, val in obj.iteritems() ])
    if isinstance(obj, (tuple, list, set, QuerySet)):
        # basic iterables
        return [_object_to_data(item, resource) for item in obj]
    if isinstance(obj, models.Manager):
        # Manager objects
        return [_object_to_data(item, resource) for item in obj.all()]
    if isinstance(obj, models.Model):
        # Model instances
        return _object_to_data(_model_to_dict(obj, resource))
    if isinstance(obj, decimal.Decimal):
        # Decimals (force to string representation)
        return str(obj)
    if inspect.isfunction(obj) and not inspect.getargspec(obj)[0]:
        # function with no args
        return _object_to_data(obj(), resource)
    if inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) <= 1:
        # bound method
        return _object_to_data(obj(), resource)

    return smart_unicode(obj, strings_only=True)


class BaseResource(object):
    """
    Base class for all Resource classes, which simply defines the interface they provide.
    """
    fields = None
    include = None
    exclude = None

    def __init__(self, view):
        self.view = view

    def validate_request(self, data, files):
        """
        Given the request data return the cleaned, validated content.
        Typically raises a ErrorResponse with status code 400 (Bad Request) on failure.
        """
        return data
    
    def filter_response(self, obj):
        """
        Given the response content, filter it into a serializable object.
        """
        return _object_to_data(obj, self)


class Resource(BaseResource):
    """
    A Resource determines how a python object maps to some serializable data.
    Objects that a resource can act on include plain Python object instances, Django Models, and Django QuerySets.
    """
    
    # The model attribute refers to the Django Model which this Resource maps to.
    # (The Model's class, rather than an instance of the Model)
    model = None
    
    # By default the set of returned fields will be the set of:
    #
    # 0. All the fields on the model, excluding 'id'.
    # 1. All the properties on the model.
    # 2. The absolute_url of the model, if a get_absolute_url method exists for the model.
    #
    # If you wish to override this behaviour,
    # you should explicitly set the fields attribute on your class.
    fields = None


class FormResource(Resource):
    """
    Resource class that uses forms for validation.
    Also provides a get_bound_form() method which may be used by some renderers.

    On calling validate() this validator may set a `.bound_form_instance` attribute on the
    view, which may be used by some renderers.
    """
    form = None

    def validate_request(self, data, files):
        """
        Given some content as input return some cleaned, validated content.
        Raises a ErrorResponse with status code 400 (Bad Request) on failure.
        
        Validation is standard form validation, with an additional constraint that no extra unknown fields may be supplied.

        On failure the ErrorResponse content is a dict which may contain 'errors' and 'field-errors' keys.
        If the 'errors' key exists it is a list of strings of non-field errors.
        If the 'field-errors' key exists it is a dict of {field name as string: list of errors as strings}.
        """
        return self._validate(data, files)


    def _validate(self, data, files, allowed_extra_fields=()):
        """
        Wrapped by validate to hide the extra_fields option that the ModelValidatorMixin uses.
        extra_fields is a list of fields which are not defined by the form, but which we still
        expect to see on the input.
        """
        bound_form = self.get_bound_form(data, files)

        if bound_form is None:
            return data
        
        self.view.bound_form_instance = bound_form

        seen_fields_set = set(data.keys())
        form_fields_set = set(bound_form.fields.keys())
        allowed_extra_fields_set = set(allowed_extra_fields)

        # In addition to regular validation we also ensure no additional fields are being passed in...
        unknown_fields = seen_fields_set - (form_fields_set | allowed_extra_fields_set)

        # Check using both regular validation, and our stricter no additional fields rule
        if bound_form.is_valid() and not unknown_fields:
            # Validation succeeded...
            cleaned_data = bound_form.cleaned_data

            cleaned_data.update(bound_form.files)

            # Add in any extra fields to the cleaned content...
            for key in (allowed_extra_fields_set & seen_fields_set) - set(cleaned_data.keys()):
                cleaned_data[key] = data[key]

            return cleaned_data

        # Validation failed...
        detail = {}

        if not bound_form.errors and not unknown_fields:
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
                detail[u'field-errors'] = field_errors

        # Return HTTP 400 response (BAD REQUEST)
        raise ErrorResponse(400, detail)
  

    def get_bound_form(self, data=None, files=None):
        """
        Given some content return a Django form bound to that content.
        If form validation is turned off (form class attribute is None) then returns None.
        """
        if not self.form:
            return None

        if data is not None:
            return self.form(data, files)

        return self.form()


class ModelResource(FormResource):
    """
    Resource class that uses forms for validation and otherwise falls back to a model form if no form is set.
    Also provides a get_bound_form() method which may be used by some renderers.
    """
 
    """The form class that should be used for validation, or None to use model form validation."""   
    form = None
    
    """The model class from which the model form should be constructed if no form is set."""
    model = None
    
    """The list of fields we expect to receive as input.  Fields in this list will may be received with
    raising non-existent field errors, even if they do not exist as fields on the ModelForm.

    Setting the fields class attribute causes the exclude class attribute to be disregarded."""
    fields = None
    
    """The list of fields to exclude from the Model.  This is only used if the fields class attribute is not set."""
    exclude = ('id', 'pk')
    

    # TODO: test the different validation here to allow for get get_absolute_url to be supplied on input and not bork out
    # TODO: be really strict on fields - check they match in the handler methods. (this isn't a validator thing tho.)
    def validate_request(self, data, files):
        """
        Given some content as input return some cleaned, validated content.
        Raises a ErrorResponse with status code 400 (Bad Request) on failure.
        
        Validation is standard form or model form validation,
        with an additional constraint that no extra unknown fields may be supplied,
        and that all fields specified by the fields class attribute must be supplied,
        even if they are not validated by the form/model form.

        On failure the ErrorResponse content is a dict which may contain 'errors' and 'field-errors' keys.
        If the 'errors' key exists it is a list of strings of non-field errors.
        If the 'field-errors' key exists it is a dict of {field name as string: list of errors as strings}.
        """
        return self._validate(data, files, allowed_extra_fields=self._property_fields_set)


    def get_bound_form(self, content=None):
        """Given some content return a Django form bound to that content.

        If the form class attribute has been explicitly set then use that class to create a Form,
        otherwise if model is set use that class to create a ModelForm, otherwise return None."""

        if self.form:
            # Use explict Form
            return super(ModelFormValidator, self).get_bound_form(data, files)

        elif self.model:
            # Fall back to ModelForm which we create on the fly
            class OnTheFlyModelForm(forms.ModelForm):
                class Meta:
                    model = self.model
                    #fields = tuple(self._model_fields_set)

            # Instantiate the ModelForm as appropriate
            if content and isinstance(content, models.Model):
                # Bound to an existing model instance
                return OnTheFlyModelForm(instance=content)
            elif content is not None:
                return OnTheFlyModelForm(content)
            return OnTheFlyModelForm()

        # Both form and model not set?  Okay bruv, whatevs...
        return None
    

    def url(self, instance):
        """
        Attempts to reverse resolve the url of the given model instance for this resource.
        """

        # dis does teh magicks...
        urlconf = get_urlconf()
        resolver = get_resolver(urlconf)

        possibilities = resolver.reverse_dict.getlist(self.view_callable[0])
        for tuple_item in possibilities:
            possibility = tuple_item[0]
            # pattern = tuple_item[1]
            # Note: defaults = tuple_item[2] for django >= 1.3
            for result, params in possibility:
                instance_attrs = dict([ (param, getattr(instance, param)) for param in params if hasattr(instance, param) ])
                try:
                    return reverse(self.view_callable[0], kwargs=instance_attrs)
                except NoReverseMatch:
                    pass
        raise NoReverseMatch


    @property
    def _model_fields_set(self):
        """
        Return a set containing the names of validated fields on the model.
        """
        model_fields = set(field.name for field in self.model._meta.fields)

        if fields:
            return model_fields & set(as_tuple(self.fields))

        return model_fields - set(as_tuple(self.exclude))
    
    @property
    def _property_fields_set(self):
        """
        Returns a set containing the names of validated properties on the model.
        """
        property_fields = set(attr for attr in dir(self.model) if
                              isinstance(getattr(self.model, attr, None), property)
                              and not attr.startswith('_'))

        if fields:
            return property_fields & set(as_tuple(self.fields))

        return property_fields - set(as_tuple(self.exclude))
