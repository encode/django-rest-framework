def method_overridden(method_name, klass, instance):
    """
    Determine if a method has been overridden.
    """
    method = getattr(klass, method_name)
    default_method = getattr(method, '__func__', method)  # Python 3 compat
    return default_method is not getattr(instance, method_name).__func__
