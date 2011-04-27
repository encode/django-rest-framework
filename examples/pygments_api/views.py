from __future__ import with_statement  # for python 2.5
from django.conf import settings
from django.core.urlresolvers import reverse

from djangorestframework.resource import Resource
from djangorestframework.response import Response
from djangorestframework.emitters import BaseEmitter
from djangorestframework import status

from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments import highlight

from forms import PygmentsForm

import os
import uuid
import operator

# We need somewhere to store the code that we highlight
HIGHLIGHTED_CODE_DIR = os.path.join(settings.MEDIA_ROOT, 'pygments')
MAX_FILES = 10

def list_dir_sorted_by_ctime(dir):
    """Return a list of files sorted by creation time"""
    filepaths = [os.path.join(dir, file) for file in os.listdir(dir) if not file.startswith('.')]
    return [item[0] for item in sorted([(path, os.path.getctime(path)) for path in filepaths],
                                                     key=operator.itemgetter(1), reverse=False)]
def remove_oldest_files(dir, max_files):
    """Remove the oldest files in a directory 'dir', leaving at most 'max_files' remaining.
    We use this to limit the number of resources in the sandbox."""
    [os.remove(path) for path in list_dir_sorted_by_ctime(dir)[max_files:]]


class HTMLEmitter(BaseEmitter):
    """Basic emitter which just returns the content without any further serialization."""
    media_type = 'text/html'


class PygmentsRoot(Resource):
    """This example demonstrates a simple RESTful Web API aound the awesome pygments library.
    This top level resource is used to create highlighted code snippets, and to list all the existing code snippets."""
    form = PygmentsForm
    allowed_methods = anon_allowed_methods = ('GET', 'POST',)

    def get(self, request, auth):
        """Return a list of all currently existing snippets."""
        unique_ids = [os.path.split(f)[1] for f in list_dir_sorted_by_ctime(HIGHLIGHTED_CODE_DIR)]
        return [reverse('pygments-instance', args=[unique_id]) for unique_id in unique_ids]

    def post(self, request, auth, content):
        """Create a new highlighed snippet and return it's location.
        For the purposes of the sandbox example, also ensure we delete the oldest snippets if we have > MAX_FILES."""
        unique_id = str(uuid.uuid1())
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)

        lexer = get_lexer_by_name(content['lexer'])
        linenos = 'table' if content['linenos'] else False
        options = {'title': content['title']} if content['title'] else {}
        formatter = HtmlFormatter(style=content['style'], linenos=linenos, full=True, **options)
        
        with open(pathname, 'w') as outfile:
            highlight(content['code'], lexer, formatter, outfile)
        
        remove_oldest_files(HIGHLIGHTED_CODE_DIR, MAX_FILES)

        return Response(status.HTTP_201_CREATED, headers={'Location': reverse('pygments-instance', args=[unique_id])})


class PygmentsInstance(Resource):
    """Simply return the stored highlighted HTML file with the correct mime type.
    This Resource only emits HTML and uses a standard HTML emitter rather than the emitters.DocumentingHTMLEmitter class."""
    allowed_methods = anon_allowed_methods = ('GET',)
    emitters = (HTMLEmitter,)

    def get(self, request, auth, unique_id):
        """Return the highlighted snippet."""
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)
        if not os.path.exists(pathname):
            return Resource(status.HTTP_404_NOT_FOUND)
        return open(pathname, 'r').read()

    def delete(self, request, auth, unique_id):
        """Delete the highlighted snippet."""
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)
        if not os.path.exists(pathname):
            return Resource(status.HTTP_404_NOT_FOUND)
        return os.remove(pathname)

