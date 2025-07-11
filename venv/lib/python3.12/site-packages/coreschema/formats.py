import re


email_pattern = re.compile('^[^@]+@[^@]')
uri_pattern = re.compile('^[A-Za-z][A-Za-z0-9+.-]+:')


def validate_format(value, format):
    function = {
        'email': validate_email,
        'uri': validate_uri
    }.get(format, unknown_format)
    return function(value)


def unknown_format(value):
    return value


def validate_email(value):
    return bool(re.match(email_pattern, value))


def validate_uri(value):
    return bool(re.match(uri_pattern, value))
