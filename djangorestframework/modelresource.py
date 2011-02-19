from django.forms import ModelForm
from django.db.models import Model
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField

from djangorestframework.response import Response, ResponseException
from djangorestframework.resource import Resource
from djangorestframework.validators import ModelFormValidatorMixin
from djangorestframework import status

import decimal
import inspect
import re


class ModelResource(Resource, ModelFormValidatorMixin):
    """A specialized type of Resource, for resources that map directly to a Django Model.
    Useful things this provides:

    0. Default input validation based on ModelForms.
    1. Nice serialization of returned Models and QuerySets.
    2. A default set of create/read/update/delete operations."""
    
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
    
    # By default the form used with be a ModelForm for self.model
    # If you wish to override this behaviour or provide a sub-classed ModelForm
    # you should explicitly set the form attribute on your class.
    form = None
    
    # By default the set of input fields will be the same as the set of output fields
    # If you wish to override this behaviour you should explicitly set the
    # form_fields attribute on your class. 
    #form_fields = None


    #def get_form(self, content=None):
    #    """Return a form that may be used in validation and/or rendering an html emitter"""
    #    if self.form:
    #        return super(self.__class__, self).get_form(content)
    #
    #    elif self.model:
    #
    #        class NewModelForm(ModelForm):
    #            class Meta:
    #                model = self.model
    #                fields = self.form_fields if self.form_fields else None
    #
    #        if content and isinstance(content, Model):
    #            return NewModelForm(instance=content)
    #        elif content:
    #            return NewModelForm(content)
    #        
    #        return NewModelForm()
    #
    #    return None


    #def cleanup_request(self, data, form_instance):
    #    """Override cleanup_request to drop read-only fields from the input prior to validation.
    #    This ensures that we don't error out with 'non-existent field' when these fields are supplied,
    #    and allows for a pragmatic approach to resources which include read-only elements.
    #
    #    I would actually like to be strict and verify the value of correctness of the values in these fields,
    #    although that gets tricky as it involves validating at the point that we get the model instance.
    #    
    #    See here for another example of this approach:
    #    http://fedoraproject.org/wiki/Cloud_APIs_REST_Style_Guide
    #    https://www.redhat.com/archives/rest-practices/2010-April/thread.html#00041"""
    #    read_only_fields = set(self.fields) - set(self.form_instance.fields)
    #    input_fields = set(data.keys())
    #
    #    clean_data = {}
    #    for key in input_fields - read_only_fields:
    #        clean_data[key] = data[key]
    #
    #    return super(ModelResource, self).cleanup_request(clean_data, form_instance)


    def cleanup_response(self, data):
        """A munging of Piston's pre-serialization.  Returns a dict"""

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
            elif isinstance(thing, Model):
                ret = _model(thing, fields=fields)
            #elif isinstance(thing, HttpResponse):    TRC
            #    raise HttpStatusCode(thing)
            elif inspect.isfunction(thing):
                if not inspect.getargspec(thing)[0]:
                    ret = _any(thing())
            elif hasattr(thing, '__emittable__'):
                f = thing.__emittable__
                if inspect.ismethod(f) and len(inspect.getargspec(f)[0]) == 1:
                    ret = _any(f())
            else:
                ret = str(thing)  # TRC  TODO: Change this back!

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
            
            if handler or fields:
                v = lambda f: getattr(data, f.attname)

                if not fields:
                    """
                    Fields was not specified, try to find teh correct
                    version in the typemapper we were sent.
                    """
                    mapped = self.in_typemapper(type(data), self.anonymous)
                    get_fields = set(mapped.fields)
                    exclude_fields = set(mapped.exclude).difference(get_fields)
                
                    if not get_fields:
                        get_fields = set([ f.attname.replace("_id", "", 1)
                            for f in data._meta.fields ])
                
                    # sets can be negated.
                    for exclude in exclude_fields:
                        if isinstance(exclude, basestring):
                            get_fields.discard(exclude)
                            
                        elif isinstance(exclude, re._pattern_type):
                            for field in get_fields.copy():
                                if exclude.match(field):
                                    get_fields.discard(field)
                    
                    get_absolute_url = True

                else:
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
        return _any(data, self.fields)


    def post(self, request, auth, content, *args, **kwargs):
        # TODO: test creation on a non-existing resource url
        
        # translated related_field into related_field_id
        for related_name in [field.name for field in self.model._meta.fields if isinstance(field, RelatedField)]:
            if kwargs.has_key(related_name):
                kwargs[related_name + '_id'] = kwargs[related_name]
                del kwargs[related_name]

        all_kw_args = dict(content.items() + kwargs.items())
        if args:
            instance = self.model(pk=args[-1], **all_kw_args)
        else:
            instance = self.model(**all_kw_args)
        instance.save()
        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = instance.get_absolute_url()
        return Response(status.HTTP_201_CREATED, instance, headers)

    def get(self, request, auth, *args, **kwargs):
        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                instance = self.model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                instance = self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            raise ResponseException(status.HTTP_404_NOT_FOUND)

        return instance

    def put(self, request, auth, content, *args, **kwargs):
        # TODO: update on the url of a non-existing resource url doesn't work correctly at the moment - will end up with a new url 
        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                instance = self.model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                instance = self.model.objects.get(**kwargs)

            for (key, val) in content.items():
                setattr(instance, key, val)
        except self.model.DoesNotExist:
            instance = self.model(**content)
            instance.save()

        instance.save()
        return instance

    def delete(self, request, auth, *args, **kwargs):
        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                instance = self.model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                instance = self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            raise ResponseException(status.HTTP_404_NOT_FOUND, None, {})

        instance.delete()
        return
        

class RootModelResource(ModelResource):
    """A Resource which provides default operations for list and create."""
    allowed_methods = ('GET', 'POST')
    queryset = None

    def get(self, request, auth, *args, **kwargs):
        queryset = self.queryset if self.queryset else self.model.objects.all()
        return queryset.filter(**kwargs)


class QueryModelResource(ModelResource):
    """Resource with default operations for list.
    TODO: provide filter/order/num_results/paging, and a create operation to create queries."""
    allowed_methods = ('GET',)
    queryset = None

    def get_form(self, data=None):
        return None

    def get(self, request, auth, *args, **kwargs):
        queryset = self.queryset if self.queryset else self.model.objects.all()
        return queryset.filer(**kwargs)

