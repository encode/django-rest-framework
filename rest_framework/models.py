import inspect

from django.db import models


def resolve_model(obj):
    """
    Resolve supplied `obj` to a Django model class.

    `obj` must be a Django model class, or a string representation
    of one.

    String representations should have the format:
        'appname.ModelName'
    """
    if type(obj) == str and len(obj.split('.')) == 2:
        app_name, model_name = obj.split('.')
        return models.get_model(app_name, model_name)
    elif inspect.isclass(obj) and issubclass(obj, models.Model):
        return obj
    else:
        raise ValueError("{0} is not a valid Django model".format(obj))
