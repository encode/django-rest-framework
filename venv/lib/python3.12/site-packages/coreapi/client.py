from coreapi import codecs, exceptions, transports
from coreapi.compat import string_types
from coreapi.document import Document, Link
from coreapi.utils import determine_transport, get_installed_codecs
import collections
import itypes


LinkAncestor = collections.namedtuple('LinkAncestor', ['document', 'keys'])


def _lookup_link(document, keys):
    """
    Validates that keys looking up a link are correct.

    Returns a two-tuple of (link, link_ancestors).
    """
    if not isinstance(keys, (list, tuple)):
        msg = "'keys' must be a list of strings or ints."
        raise TypeError(msg)
    if any([
        not isinstance(key, string_types) and not isinstance(key, int)
        for key in keys
    ]):
        raise TypeError("'keys' must be a list of strings or ints.")

    # Determine the link node being acted on, and its parent document.
    # 'node' is the link we're calling the action for.
    # 'document_keys' is the list of keys to the link's parent document.
    node = document
    link_ancestors = [LinkAncestor(document=document, keys=[])]
    for idx, key in enumerate(keys):
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
            msg = 'Index %s did not reference a link. Key %s was not found.'
            raise exceptions.LinkLookupError(msg % (index_string, repr(key).strip('u')))
        if isinstance(node, Document):
            ancestor = LinkAncestor(document=node, keys=keys[:idx + 1])
            link_ancestors.append(ancestor)

    # Ensure that we've correctly indexed into a link.
    if not isinstance(node, Link):
        index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
        msg = "Can only call 'action' on a Link. Index %s returned type '%s'."
        raise exceptions.LinkLookupError(
            msg % (index_string, type(node).__name__)
        )

    return (node, link_ancestors)


def _validate_parameters(link, parameters):
    """
    Ensure that parameters passed to the link are correct.
    Raises a `ParameterError` if any parameters do not validate.
    """
    provided = set(parameters.keys())
    required = set([
        field.name for field in link.fields if field.required
    ])
    optional = set([
        field.name for field in link.fields if not field.required
    ])

    errors = {}

    # Determine if any required field names not supplied.
    missing = required - provided
    for item in missing:
        errors[item] = 'This parameter is required.'

    # Determine any parameter names supplied that are not valid.
    unexpected = provided - (optional | required)
    for item in unexpected:
        errors[item] = 'Unknown parameter.'

    if errors:
        raise exceptions.ParameterError(errors)


def get_default_decoders():
    return [
        codecs.CoreJSONCodec(),
        codecs.JSONCodec(),
        codecs.TextCodec(),
        codecs.DownloadCodec()
    ]


def get_default_transports(auth=None, session=None):
    return [
        transports.HTTPTransport(auth=auth, session=session)
    ]


class Client(itypes.Object):
    def __init__(self, decoders=None, transports=None, auth=None, session=None):
        assert transports is None or auth is None, (
            "Cannot specify both 'auth' and 'transports'. "
            "When specifying transport instances explicitly you should set "
            "the authentication directly on the transport."
        )
        if decoders is None:
            decoders = get_default_decoders()
        if transports is None:
            transports = get_default_transports(auth=auth)
        self._decoders = itypes.List(decoders)
        self._transports = itypes.List(transports)

    @property
    def decoders(self):
        return self._decoders

    @property
    def transports(self):
        return self._transports

    def get(self, url, format=None, force_codec=False):
        link = Link(url, action='get')

        decoders = self.decoders
        if format:
            force_codec = True
            decoders = [decoder for decoder in self.decoders if decoder.format == format]
            if not decoders:
                installed_codecs = get_installed_codecs()
                if format in installed_codecs:
                    decoders = [installed_codecs[format]]
                else:
                    raise ValueError("No decoder available with format='%s'" % format)

        # Perform the action, and return a new document.
        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, decoders, force_codec=force_codec)

    def reload(self, document, format=None, force_codec=False):
        # Fallback for v1.x. To be removed in favour of explict `get` style.
        return self.get(document.url, format=format, force_codec=force_codec)

    def action(self, document, keys, params=None, validate=True, overrides=None,
               action=None, encoding=None, transform=None):
        if (action is not None) or (encoding is not None) or (transform is not None):
            # Fallback for v1.x overrides.
            # Will be removed at some point, most likely in a 2.1 release.
            if overrides is None:
                overrides = {}
            if action is not None:
                overrides['action'] = action
            if encoding is not None:
                overrides['encoding'] = encoding
            if transform is not None:
                overrides['transform'] = transform

        if isinstance(keys, string_types):
            keys = [keys]

        if params is None:
            params = {}

        # Validate the keys and link parameters.
        link, link_ancestors = _lookup_link(document, keys)
        if validate:
            _validate_parameters(link, params)

        if overrides:
            # Handle any explicit overrides.
            url = overrides.get('url', link.url)
            action = overrides.get('action', link.action)
            encoding = overrides.get('encoding', link.encoding)
            transform = overrides.get('transform', link.transform)
            fields = overrides.get('fields', link.fields)
            link = Link(url, action=action, encoding=encoding, transform=transform, fields=fields)

        # Perform the action, and return a new document.
        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, self.decoders, params=params, link_ancestors=link_ancestors)
