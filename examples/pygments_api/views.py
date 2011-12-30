from __future__ import with_statement  # for python 2.5
from django.conf import settings
from django.core.urlresolvers import reverse

from djangorestframework.resources import FormResource
from djangorestframework.response import Response
from djangorestframework.renderers import BaseRenderer
from djangorestframework.views import View
from djangorestframework import status

from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments import highlight

from forms import PygmentsForm

import os
import uuid
import operator

# We need somewhere to store the code snippets that we highlight
HIGHLIGHTED_CODE_DIR = os.path.join(settings.MEDIA_ROOT, 'pygments')
MAX_FILES = 10

if not os.path.exists(HIGHLIGHTED_CODE_DIR):
    os.makedirs(HIGHLIGHTED_CODE_DIR)


def list_dir_sorted_by_ctime(dir):
    """
    Return a list of files sorted by creation time
    """
    filepaths = [os.path.join(dir, file) for file in os.listdir(dir) if not file.startswith('.')]
    return [item[0] for item in sorted( [(path, os.path.getctime(path)) for path in filepaths],
                                        key=operator.itemgetter(1), reverse=False) ]

def remove_oldest_files(dir, max_files):
    """
    Remove the oldest files in a directory 'dir', leaving at most 'max_files' remaining.
    We use this to limit the number of resources in the sandbox.
    """
    [os.remove(path) for path in list_dir_sorted_by_ctime(dir)[max_files:]]


class HTMLRenderer(BaseRenderer):
    """
    Basic renderer which just returns the content without any further serialization.
    """
    media_type = 'text/html'


class PygmentsRoot(View):
    """
    This example demonstrates a simple RESTful Web API around the awesome pygments library.
    This top level resource is used to create highlighted code snippets, and to list all the existing code snippets.
    """
    form = PygmentsForm

    def get(self, request):
        """
        Return a list of all currently existing snippets.
        """
        unique_ids = [os.path.split(f)[1] for f in list_dir_sorted_by_ctime(HIGHLIGHTED_CODE_DIR)]
        return [reverse('pygments-instance', args=[unique_id]) for unique_id in unique_ids]

    def post(self, request):
        """
        Create a new highlighed snippet and return it's location.
        For the purposes of the sandbox example, also ensure we delete the oldest snippets if we have > MAX_FILES.
        """
        unique_id = str(uuid.uuid1())
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)

        lexer = get_lexer_by_name(self.CONTENT['lexer'])
        linenos = 'table' if self.CONTENT['linenos'] else False
        options = {'title': self.CONTENT['title']} if self.CONTENT['title'] else {}
        formatter = HtmlFormatter(style=self.CONTENT['style'], linenos=linenos, full=True, **options)

        with open(pathname, 'w') as outfile:
            highlight(self.CONTENT['code'], lexer, formatter, outfile)

        remove_oldest_files(HIGHLIGHTED_CODE_DIR, MAX_FILES)

        return Response(status.HTTP_201_CREATED, headers={'Location': reverse('pygments-instance', args=[unique_id])})


class PygmentsInstance(View):
    """
    Simply return the stored highlighted HTML file with the correct mime type.
    This Resource only renders HTML and uses a standard HTML renderer rather than the renderers.DocumentingHTMLRenderer class.
    """
    renderers = (HTMLRenderer,)

    def get(self, request, unique_id):
        """
        Return the highlighted snippet.
        """
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)
        if not os.path.exists(pathname):
            return Response(status.HTTP_404_NOT_FOUND)
        return open(pathname, 'r').read()

    def delete(self, request, unique_id):
        """
        Delete the highlighted snippet.
        """
        pathname = os.path.join(HIGHLIGHTED_CODE_DIR, unique_id)
        if not os.path.exists(pathname):
            return Response(status.HTTP_404_NOT_FOUND)
        return os.remove(pathname)

