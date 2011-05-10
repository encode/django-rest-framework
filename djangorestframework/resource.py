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
        ret = [_object_to_data(item) for item in obj.all()]
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


# TODO: Replace this with new Serializer code based on Forms API.

#class Resource(object):
#    def __init__(self, view):
#        self.view = view
#    
#    def object_to_data(self, obj):
#        pass
#    
#    def data_to_object(self, data, files):
#        pass
#
#class FormResource(object):
#    pass
#
#class ModelResource(object):
#    pass


class Resource(object):
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

    @classmethod
    def object_to_serializable(self, data):
        """A (horrible) munging of Piston's pre-serialization.  Returns a dict"""

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
        return _any(data, self.fields)

