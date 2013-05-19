"""Attribute checking for Python classes
"""

class InvalidAttributeError(AttributeError):
    """
    Use this for invalid attributes because AttributeError means not found
    """

    pass


class ValidatorMeta(type):
    """
    Metaclass to guard against setting unrecognized attributes
    Set it as __metaclass__ as low in the inheritance chain as possible
    """
    def __new__(cls, name, parents, kwargs):
        """Creates the new class, and sees if it has only known attributes
        """
        new_cls = type.__new__(cls, name, parents, kwargs)

        ## Fail only if the new class defines an api
        if not new_cls.__dict__.has_key('valid_attributes'):
            return new_cls

        ## Do some sanity checks to not fail in vain
        for attr, val in kwargs.items():
            if attr == 'valid_attributes':
                continue
            if attr.startswith('_'):
                continue
            # Methods are always allowed
            if callable(val):
                continue

            # Ensure validity
            if not attr in new_cls.valid_attributes:
                raise InvalidAttributeError(attr)

        return new_cls

