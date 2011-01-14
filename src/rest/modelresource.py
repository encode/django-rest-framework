"""TODO: docs
"""
from django.forms import ModelForm
from django.db.models.query import QuerySet
from django.db.models import Model

from rest.resource import Resource

import decimal
import inspect
import re


class ModelResource(Resource):
    model = None
    fields = None
    form_fields = None

    def get_bound_form(self, data=None, is_response=False):
        """Return a form that may be used in validation and/or rendering an html emitter"""
        if self.form:
            return super(self.__class__, self).get_bound_form(data, is_response=is_response)

        elif self.model:
            class NewModelForm(ModelForm):
                class Meta:
                    model = self.model
                    fields = self.form_fields if self.form_fields else None #self.fields
                    
            if data and not is_response:
                return NewModelForm(data)
            elif data and is_response:
                return NewModelForm(instance=data)
            else:
                return NewModelForm()
        
        else:
            return None
    


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
            
            for key, val in ret.items():
                if key.endswith('_url') or key.endswith('_uri'):
                    ret[key] = self.add_domain(val)

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


    def create(self, data, headers={}, *args, **kwargs):
        # TODO: test creation on a non-existing resource url
        all_kw_args = dict(data.items() + kwargs.items())
        instance = self.model(**all_kw_args)
        instance.save()
        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = self.add_domain(instance.get_absolute_url())
        return (201, instance, headers)

    def read(self, headers={}, *args, **kwargs):
        try:
            instance = self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return (404, None, {})

        return (200, instance, {})

    def update(self, data, headers={}, *args, **kwargs):
        # TODO: update on the url of a non-existing resource url doesn't work correctly at the moment - will end up with a new url 
        try:
            instance = self.model.objects.get(**kwargs)    
            for (key, val) in data.items():
                setattr(instance, key, val)
        except self.model.DoesNotExist:
            instance = self.model(**data)
            instance.save()

        instance.save()
        return (200, instance, {})

    def delete(self, headers={}, *args, **kwargs):
        try:
            instance = self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return (404, None, {})

        instance.delete()
        return (204, None, {})
        


class QueryModelResource(ModelResource):
    allowed_methods = ('read',)
    queryset = None

    def get_bound_form(self, data=None, is_response=False):
        return None

    def read(self, headers={}, *args, **kwargs):
        if self.queryset:
            return (200, self.queryset, {})
        queryset = self.model.objects.all()
        return (200, queryset, {})

