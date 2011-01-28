from django.conf import settings

from flywheel.resource import Resource
from flywheel.response import Response, status
from flywheel.emitters import BaseEmitter

from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments import highlight

from forms import PygmentsForm

import os
import hashlib

# We need somewhere to store the code that we highlight
HIGHLIGHTED_CODE_DIR = os.path.join(settings.MEDIA_ROOT, 'pygments')


class HTMLEmitter(BaseEmitter):
    """Basic emitter which just returns the content without any further serialization."""
    media_type = 'text/html'


class PygmentsRoot(Resource):
    """This example demonstrates a simple RESTful Web API aound the awesome pygments library.
    This top level resource is used to create  """
    form = PygmentsForm
    allowed_methods = anon_allowed_methods = ('POST',)

    def post(self, request, auth, content):
        # Generate a unique id by hashing the input
        input_str = ''.join(['%s%s' % (key, content[key]) for key in sorted(content.keys())])
        hash = hashlib.md5()
        hash.update(input_str)
        unique_id = hash.hexdigest()
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)

        if not os.path.exists(pathname):
            # We only need to generate the file if it doesn't already exist.
            options = {'title': content['title']} if content['title'] else {}
            linenos = 'table' if content['linenos'] else False
            lexer = get_lexer_by_name(content['lexer'])
            formatter = HtmlFormatter(style=content['style'], linenos=linenos, full=True, **options)
            
            with open(pathname, 'w') as outfile:
                highlight(content['code'], lexer, formatter, outfile)
            
        return Response(status.HTTP_201_CREATED, headers={'Location': self.reverse(PygmentsInstance, unique_id)})


class PygmentsInstance(Resource):
    """Simply return the stored highlighted HTML file with the correct mime type.
    This Resource only emits HTML and uses a standard HTML emitter rather than FlyWheel's DocumentingHTMLEmitter class."""
    allowed_methods = anon_allowed_methods = ('GET',)
    emitters = (HTMLEmitter,)

    def get(self, request, auth, unique_id):
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)
        if not os.path.exists(pathname):
            return Resource(status.HTTP_404_NOT_FOUND)
        return open(pathname, 'r').read()


