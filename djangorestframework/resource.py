from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField
from django.utils.encoding import smart_unicode

import decimal
import inspect
import re



def _model_to_dict(instance, fields=None, exclude=None):
    """
    This is a clone of Django's ``django.forms.model_to_dict`` except that it
    doesn't coerce related objects into primary keys.
    """
    opts = instance._meta
    data = {}
    for f in opts.fields + opts.many_to_many:
        if not f.editable:
            continue
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, models.ForeignKey):
            data[f.name] = getattr(instance, f.name)
        else:
            data[f.name] = f.value_from_object(instance)
    return data


def _object_to_data(obj):
    """
    Convert an object into a serializable representation.
    """
    if isinstance(obj, dict):
        # dictionaries
        return dict([ (key, _object_to_data(val)) for key, val in obj.iteritems() ])    
    if isinstance(obj, (tuple, list, set, QuerySet)):
        # basic iterables
        return [_object_to_data(item) for item in obj]
    if isinstance(obj, models.Manager):
        # Manager objects
        return [_object_to_data(item) for item in obj.all()]
    if isinstance(obj, models.Model):
        # Model instances
        return _object_to_data(_model_to_dict(obj))
    if isinstance(obj, decimal.Decimal):
        # Decimals (force to string representation)
        return str(obj)
    if inspect.isfunction(obj) and not inspect.getargspec(obj)[0]:
        # function with no args
        return _object_to_data(obj())
    if inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) == 1:
        # method with only a 'self' args
        return _object_to_data(obj())

    # fallback
    return smart_unicode(obj, strings_only=True)


def _form_to_data(form):
    """
    Returns a dict containing the data in a form instance.
    
    This code is pretty much a clone of the ``Form.as_p()`` ``Form.as_ul``
    and ``Form.as_table()`` methods, except that it returns data suitable
    for arbitrary serialization, rather than rendering the result directly
    into html.
    """
    ret = {}
    for name, field in form.fields.items():
        if not form.is_bound:
            data = form.initial.get(name, field.initial)
            if callable(data):
                data = data()
        else:
            if isinstance(field, FileField) and form.data is None:
                data = form.initial.get(name, field.initial)
            else:
                data = field.widget.value_from_datadict(form.data, form.files, name)
        ret[name] = field.prepare_value(data)
    return ret


class BaseResource(object):
    """Base class for all Resource classes, which simply defines the interface they provide."""

    def __init__(self, view):
        self.view = view

    def validate(self, data, files):
        """Given some content as input return some cleaned, validated content.
        Typically raises a ErrorResponse with status code 400 (Bad Request) on failure.

        Must be overridden to be implemented."""
        return data
    
    def object_to_data(self, obj):
        return _object_to_data(obj)


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

    # TODO: Replace this with new Serializer code based on Forms API.
    def object_to_data(self, obj):
        """
        A (horrible) munging of Piston's pre-serialization.  Returns a dict.
        """

        def _any(thing, fields=()):
            """
            Dispatch, all types are routed through here.
            """
            ret = None
            
            if isinstance(thing, QuerySet):
                ret = _qs(thing, fields=fields)
            elif isinstance(thing, (tuple, list)):
                ret = _list(thing)
            elif isinstance(thing, dict):
                ret = _dict(thing)
            elif isinstance(thing, int):
                ret = thing
            elif isinstance(thing, bool):
                ret = thing
            elif isinstance(thing, type(None)):
                ret = thing
            elif isinstance(thing, decimal.Decimal):
                ret = str(thing)
            elif isinstance(thing, models.Model):
                ret = _model(thing, fields=fields)
            #elif isinstance(thing, HttpResponse):    TRC
            #    raise HttpStatusCode(thing)
            elif inspect.isfunction(thing):
                if not inspect.getargspec(thing)[0]:
                    ret = _any(thing())
            elif hasattr(thing, '__rendertable__'):
                f = thing.__rendertable__
                if inspect.ismethod(f) and len(inspect.getargspec(f)[0]) == 1:
                    ret = _any(f())
            else:
                ret = unicode(thing)  # TRC

            return ret

        def _fk(data, field):
            """
            Foreign keys.
            """
            return _any(getattr(data, field.name))
        
        def _related(data, fields=()):
            """
            Foreign keys.
            """
            return [ _model(m, fields) for m in data.iterator() ]
        
        def _m2m(data, field, fields=()):
            """
            Many to many (re-route to `_model`.)
            """
            return [ _model(m, fields) for m in getattr(data, field.name).iterator() ]
        

        def _method_fields(data, fields):
            if not data:
                return { }
    
            has = dir(data)
            ret = dict()
                
            for field in fields:
                if field in has:
                    ret[field] = getattr(data, field)
            
            return ret

        def _model(data, fields=()):
            """
            Models. Will respect the `fields` and/or
            `exclude` on the handler (see `typemapper`.)
            """
            ret = { }
            #handler = self.in_typemapper(type(data), self.anonymous)  # TRC
            handler = None                                             # TRC
            get_absolute_url = False
            
            if fields:
                v = lambda f: getattr(data, f.attname)

                get_fields = set(fields)
                if 'absolute_url' in get_fields:   # MOVED (TRC)
                    get_absolute_url = True

                met_fields = _method_fields(handler, get_fields)  # TRC

                for f in data._meta.local_fields:
                    if f.serialize and not any([ p in met_fields for p in [ f.attname, f.name ]]):
                        if not f.rel:
                            if f.attname in get_fields:
                                ret[f.attname] = _any(v(f))
                                get_fields.remove(f.attname)
                        else:
                            if f.attname[:-3] in get_fields:
                                ret[f.name] = _fk(data, f)
                                get_fields.remove(f.name)
                
                for mf in data._meta.many_to_many:
                    if mf.serialize and mf.attname not in met_fields:
                        if mf.attname in get_fields:
                            ret[mf.name] = _m2m(data, mf)
                            get_fields.remove(mf.name)
                
                # try to get the remainder of fields
                for maybe_field in get_fields:
                    
                    if isinstance(maybe_field, (list, tuple)):
                        model, fields = maybe_field
                        inst = getattr(data, model, None)

                        if inst:
                            if hasattr(inst, 'all'):
                                ret[model] = _related(inst, fields)
                            elif callable(inst):
                                if len(inspect.getargspec(inst)[0]) == 1:
                                    ret[model] = _any(inst(), fields)
                            else:
                                ret[model] = _model(inst, fields)

                    elif maybe_field in met_fields:
                        # Overriding normal field which has a "resource method"
                        # so you can alter the contents of certain fields without
                        # using different names.
                        ret[maybe_field] = _any(met_fields[maybe_field](data))

                    else:                    
                        maybe = getattr(data, maybe_field, None)
                        if maybe:
                            if callable(maybe):
                                if len(inspect.getargspec(maybe)[0]) == 1:
                                    ret[maybe_field] = _any(maybe())
                            else:
                                ret[maybe_field] = _any(maybe)
                        else:
                            pass   # TRC
                            #handler_f = getattr(handler or self.handler, maybe_field, None)
                            #
                            #if handler_f:
                            #    ret[maybe_field] = _any(handler_f(data))

            else:
                # Add absolute_url if it exists
                get_absolute_url = True
                
                # Add all the fields
                for f in data._meta.fields:
                    if f.attname != 'id':
                        ret[f.attname] = _any(getattr(data, f.attname))
                
                # Add all the propertiess
                klass = data.__class__
                for attr in dir(klass):
                    if not attr.startswith('_') and not attr in ('pk','id') and isinstance(getattr(klass, attr, None), property):
                        #if attr.endswith('_url') or attr.endswith('_uri'):
                        #    ret[attr] = self.make_absolute(_any(getattr(data, attr)))
                        #else:
                        ret[attr] = _any(getattr(data, attr))
                #fields = dir(data.__class__) + ret.keys()
                #add_ons = [k for k in dir(data) if k not in fields and not k.startswith('_')]
                #print add_ons
                ###print dir(data.__class__)
                #from django.db.models import Model
                #model_fields = dir(Model)

                #for attr in dir(data):
                ##    #if attr.startswith('_'):
                ##    #    continue
                #    if (attr in fields) and not (attr in model_fields) and not attr.startswith('_'):
                #        print attr, type(getattr(data, attr, None)), attr in fields, attr in model_fields
                
                #for k in add_ons:
                #    ret[k] = _any(getattr(data, k))
            
            # TRC
            # resouce uri
            #if self.in_typemapper(type(data), self.anonymous):
            #    handler = self.in_typemapper(type(data), self.anonymous)
            #    if hasattr(handler, 'resource_uri'):
            #        url_id, fields = handler.resource_uri()
            #        ret['resource_uri'] = permalink( lambda: (url_id, 
            #            (getattr(data, f) for f in fields) ) )()
            
            # TRC
            #if hasattr(data, 'get_api_url') and 'resource_uri' not in ret:
            #    try: ret['resource_uri'] = data.get_api_url()
            #    except: pass
            
            # absolute uri
            if hasattr(data, 'get_absolute_url') and get_absolute_url:
                try: ret['absolute_url'] = data.get_absolute_url()
                except: pass
            
            #for key, val in ret.items():
            #    if key.endswith('_url') or key.endswith('_uri'):
            #        ret[key] = self.add_domain(val)

            return ret
        
        def _qs(data, fields=()):
            """
            Querysets.
            """
            return [ _any(v, fields) for v in data ]
                
        def _list(data):
            """
            Lists.
            """
            return [ _any(v) for v in data ]
            
        def _dict(data):
            """
            Dictionaries.
            """
            return dict([ (k, _any(v)) for k, v in data.iteritems() ])
            
        # Kickstart the seralizin'.
        return _any(obj, self.fields)


class FormResource(Resource):
    """Validator class that uses forms for validation.
    Also provides a get_bound_form() method which may be used by some renderers.
    
    The view class should provide `.form` attribute which specifies the form classmethod
    to be used for validation.
    
    On calling validate() this validator may set a `.bound_form_instance` attribute on the
    view, which may be used by some renderers."""


    def validate(self, data, files):
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
            field_errors = dict((key, map(unicode, val))
                for (key, val)
                in bound_form.errors.iteritems()
                if not key.startswith('__'))

            # Add any unknown field errors
            for key in unknown_fields:
                field_errors[key] = [u'This field does not exist.']
       
            if field_errors:
                detail[u'field-errors'] = field_errors

        # Return HTTP 400 response (BAD REQUEST)
        raise ErrorResponse(400, detail)
  

    def get_bound_form(self, data=None, files=None):
        """Given some content return a Django form bound to that content.
        If form validation is turned off (form class attribute is None) then returns None."""
        form_cls = getattr(self, 'form', None)

        if not form_cls:
            return None

        if data is not None:
            return form_cls(data, files)

        return form_cls()


class ModelResource(FormResource):
    """Validator class that uses forms for validation and otherwise falls back to a model form if no form is set.
    Also provides a get_bound_form() method which may be used by some renderers."""
 
    """The form class that should be used for validation, or None to use model form validation."""   
    form = None
    
    """The model class from which the model form should be constructed if no form is set."""
    model = None
    
    """The list of fields we expect to receive as input.  Fields in this list will may be received with
    raising non-existent field errors, even if they do not exist as fields on the ModelForm.

    Setting the fields class attribute causes the exclude_fields class attribute to be disregarded."""
    fields = None
    
    """The list of fields to exclude from the Model.  This is only used if the fields class attribute is not set."""
    exclude_fields = ('id', 'pk')
    

    # TODO: test the different validation here to allow for get get_absolute_url to be supplied on input and not bork out
    # TODO: be really strict on fields - check they match in the handler methods. (this isn't a validator thing tho.)
    def validate(self, data, files):
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


    def get_bound_form(self, data=None, files=None):
        """Given some content return a Django form bound to that content.

        If the form class attribute has been explicitly set then use that class to create a Form,
        otherwise if model is set use that class to create a ModelForm, otherwise return None."""

        form_cls = getattr(self, 'form', None)
        model_cls = getattr(self, 'model', None)

        if form_cls:
            # Use explict Form
            return super(ModelFormValidator, self).get_bound_form(data, files)

        elif model_cls:
            # Fall back to ModelForm which we create on the fly
            class OnTheFlyModelForm(forms.ModelForm):
                class Meta:
                    model = model_cls
                    #fields = tuple(self._model_fields_set)

            # Instantiate the ModelForm as appropriate
            if content and isinstance(content, models.Model):
                # Bound to an existing model instance
                return OnTheFlyModelForm(instance=content)
            elif not data is None:
                return OnTheFlyModelForm(data, files)
            return OnTheFlyModelForm()

        # Both form and model not set?  Okay bruv, whatevs...
        return None
    

    @property
    def _model_fields_set(self):
        """Return a set containing the names of validated fields on the model."""
        resource = self.view.resource
        model = getattr(resource, 'model', None)
        fields = getattr(resource, 'fields', self.fields)
        exclude_fields = getattr(resource, 'exclude_fields', self.exclude_fields)

        model_fields = set(field.name for field in model._meta.fields)

        if fields:
            return model_fields & set(as_tuple(fields))

        return model_fields - set(as_tuple(exclude_fields))
    
    @property
    def _property_fields_set(self):
        """Returns a set containing the names of validated properties on the model."""
        resource = self.view.resource
        model = getattr(resource, 'model', None)
        fields = getattr(resource, 'fields', self.fields)
        exclude_fields = getattr(resource, 'exclude_fields', self.exclude_fields)

        property_fields = set(attr for attr in dir(model) if
                              isinstance(getattr(model, attr, None), property)
                              and not attr.startswith('_'))

        if fields:
            return property_fields & set(as_tuple(fields))

        return property_fields - set(as_tuple(exclude_fields))
