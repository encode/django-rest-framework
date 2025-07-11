from __future__ import unicode_literals
from collections import OrderedDict
from coreapi.codecs.base import BaseCodec
from coreapi.compat import force_bytes, string_types, urlparse
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS
from coreapi.document import Document, Link, Array, Object, Error, Field
from coreapi.exceptions import ParseError
import coreschema
import json


# Schema encoding and decoding.
# Just a naive first-pass at this point.

SCHEMA_CLASS_TO_TYPE_ID = {
    coreschema.Object: 'object',
    coreschema.Array: 'array',
    coreschema.Number: 'number',
    coreschema.Integer: 'integer',
    coreschema.String: 'string',
    coreschema.Boolean: 'boolean',
    coreschema.Null: 'null',
    coreschema.Enum: 'enum',
    coreschema.Anything: 'anything'
}

TYPE_ID_TO_SCHEMA_CLASS = {
    value: key
    for key, value
    in SCHEMA_CLASS_TO_TYPE_ID.items()
}


def encode_schema_to_corejson(schema):
    type_id = SCHEMA_CLASS_TO_TYPE_ID.get(schema.__class__, 'anything')
    retval = {
        '_type': type_id,
        'title': schema.title,
        'description': schema.description
    }
    if isinstance(schema, coreschema.Enum):
        retval['enum'] = schema.enum
    return retval


def decode_schema_from_corejson(data):
    type_id = _get_string(data, '_type')
    title = _get_string(data, 'title')
    description = _get_string(data, 'description')

    kwargs = {}
    if type_id == 'enum':
        kwargs['enum'] = _get_list(data, 'enum')

    schema_cls = TYPE_ID_TO_SCHEMA_CLASS.get(type_id, coreschema.Anything)
    return schema_cls(title=title, description=description, **kwargs)


# Robust dictionary lookups, that always return an item of the correct
# type, using an empty default if an incorrect type exists.
# Useful for liberal parsing of inputs.

def _get_schema(item, key):
    schema_data = _get_dict(item, key)
    if schema_data:
        return decode_schema_from_corejson(schema_data)
    return None


def _get_string(item, key):
    value = item.get(key)
    if isinstance(value, string_types):
        return value
    return ''


def _get_dict(item, key):
    value = item.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _get_list(item, key):
    value = item.get(key)
    if isinstance(value, list):
        return value
    return []


def _get_bool(item, key):
    value = item.get(key)
    if isinstance(value, bool):
        return value
    return False


def _graceful_relative_url(base_url, url):
    """
    Return a graceful link for a URL relative to a base URL.

    * If they are the same, return an empty string.
    * If the have the same scheme and hostname, return the path & query params.
    * Otherwise return the full URL.
    """
    if url == base_url:
        return ''
    base_prefix = '%s://%s' % urlparse.urlparse(base_url or '')[0:2]
    url_prefix = '%s://%s' % urlparse.urlparse(url or '')[0:2]
    if base_prefix == url_prefix and url_prefix != '://':
        return url[len(url_prefix):]
    return url


def _escape_key(string):
    """
    The '_type' and '_meta' keys are reserved.
    Prefix with an additional '_' if they occur.
    """
    if string.startswith('_') and string.lstrip('_') in ('type', 'meta'):
        return '_' + string
    return string


def _unescape_key(string):
    """
    Unescape '__type' and '__meta' keys if they occur.
    """
    if string.startswith('__') and string.lstrip('_') in ('type', 'meta'):
        return string[1:]
    return string


def _get_content(item, base_url=None):
    """
    Return a dictionary of content, for documents, objects and errors.
    """
    return {
        _unescape_key(key): _primitive_to_document(value, base_url)
        for key, value in item.items()
        if key not in ('_type', '_meta')
    }


def _document_to_primitive(node, base_url=None):
    """
    Take a Core API document and return Python primitives
    ready to be rendered into the JSON style encoding.
    """
    if isinstance(node, Document):
        ret = OrderedDict()
        ret['_type'] = 'document'

        meta = OrderedDict()
        url = _graceful_relative_url(base_url, node.url)
        if url:
            meta['url'] = url
        if node.title:
            meta['title'] = node.title
        if node.description:
            meta['description'] = node.description
        if meta:
            ret['_meta'] = meta

        # Fill in key-value content.
        ret.update([
            (_escape_key(key), _document_to_primitive(value, base_url=url))
            for key, value in node.items()
        ])
        return ret

    elif isinstance(node, Error):
        ret = OrderedDict()
        ret['_type'] = 'error'

        if node.title:
            ret['_meta'] = {'title': node.title}

        # Fill in key-value content.
        ret.update([
            (_escape_key(key), _document_to_primitive(value, base_url=base_url))
            for key, value in node.items()
        ])
        return ret

    elif isinstance(node, Link):
        ret = OrderedDict()
        ret['_type'] = 'link'
        url = _graceful_relative_url(base_url, node.url)
        if url:
            ret['url'] = url
        if node.action:
            ret['action'] = node.action
        if node.encoding:
            ret['encoding'] = node.encoding
        if node.transform:
            ret['transform'] = node.transform
        if node.title:
            ret['title'] = node.title
        if node.description:
            ret['description'] = node.description
        if node.fields:
            ret['fields'] = [
                _document_to_primitive(field) for field in node.fields
            ]
        return ret

    elif isinstance(node, Field):
        ret = OrderedDict({'name': node.name})
        if node.required:
            ret['required'] = node.required
        if node.location:
            ret['location'] = node.location
        if node.schema:
            ret['schema'] = encode_schema_to_corejson(node.schema)
        return ret

    elif isinstance(node, Object):
        return OrderedDict([
            (_escape_key(key), _document_to_primitive(value, base_url=base_url))
            for key, value in node.items()
        ])

    elif isinstance(node, Array):
        return [_document_to_primitive(value) for value in node]

    return node


def _primitive_to_document(data, base_url=None):
    """
    Take Python primitives as returned from parsing JSON content,
    and return a Core API document.
    """
    if isinstance(data, dict) and data.get('_type') == 'document':
        # Document
        meta = _get_dict(data, '_meta')
        url = _get_string(meta, 'url')
        url = urlparse.urljoin(base_url, url)
        title = _get_string(meta, 'title')
        description = _get_string(meta, 'description')
        content = _get_content(data, base_url=url)
        return Document(
            url=url,
            title=title,
            description=description,
            media_type='application/coreapi+json',
            content=content
        )

    if isinstance(data, dict) and data.get('_type') == 'error':
        # Error
        meta = _get_dict(data, '_meta')
        title = _get_string(meta, 'title')
        content = _get_content(data, base_url=base_url)
        return Error(title=title, content=content)

    elif isinstance(data, dict) and data.get('_type') == 'link':
        # Link
        url = _get_string(data, 'url')
        url = urlparse.urljoin(base_url, url)
        action = _get_string(data, 'action')
        encoding = _get_string(data, 'encoding')
        transform = _get_string(data, 'transform')
        title = _get_string(data, 'title')
        description = _get_string(data, 'description')
        fields = _get_list(data, 'fields')
        fields = [
            Field(
                name=_get_string(item, 'name'),
                required=_get_bool(item, 'required'),
                location=_get_string(item, 'location'),
                schema=_get_schema(item, 'schema')
            )
            for item in fields if isinstance(item, dict)
        ]
        return Link(
            url=url, action=action, encoding=encoding, transform=transform,
            title=title, description=description, fields=fields
        )

    elif isinstance(data, dict):
        # Map
        content = _get_content(data, base_url=base_url)
        return Object(content)

    elif isinstance(data, list):
        # Array
        content = [_primitive_to_document(item, base_url) for item in data]
        return Array(content)

    # String, Integer, Number, Boolean, null.
    return data


class CoreJSONCodec(BaseCodec):
    media_type = 'application/coreapi+json'
    format = 'corejson'

    # The following is due to be deprecated...
    media_types = ['application/coreapi+json', 'application/vnd.coreapi+json']

    def decode(self, bytestring, **options):
        """
        Takes a bytestring and returns a document.
        """
        base_url = options.get('base_url')

        try:
            data = json.loads(bytestring.decode('utf-8'))
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

        doc = _primitive_to_document(data, base_url)

        if isinstance(doc, Object):
            doc = Document(content=dict(doc))
        elif not (isinstance(doc, Document) or isinstance(doc, Error)):
            raise ParseError('Top level node should be a document or error.')

        return doc

    def encode(self, document, **options):
        """
        Takes a document and returns a bytestring.
        """
        indent = options.get('indent')

        if indent:
            kwargs = {
                'ensure_ascii': False,
                'indent': 4,
                'separators': VERBOSE_SEPARATORS
            }
        else:
            kwargs = {
                'ensure_ascii': False,
                'indent': None,
                'separators': COMPACT_SEPARATORS
            }

        data = _document_to_primitive(document)
        return force_bytes(json.dumps(data, **kwargs))
