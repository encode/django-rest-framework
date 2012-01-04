from django.test import TestCase
from django.utils import simplejson as json

from djangorestframework.compat import RequestFactory

from pygments_api import views
import tempfile, shutil



class TestPygmentsExample(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.temp_dir = tempfile.mkdtemp()
        views.HIGHLIGHTED_CODE_DIR = self.temp_dir
        
    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
        
    def test_get_to_root(self):
        '''Just do a get on the base url'''
        request = self.factory.get('/pygments')
        view = views.PygmentsRoot.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_snippets_datetime_sorted(self):
        '''Pygments examples should be datetime sorted'''
        locations = []
        for snippet in 'abcdefghij': # String length must not exceed views.MAX_FILES, otherwise test fails
            form_data = {'code': '%s' % snippet, 'style':'friendly', 'lexer':'python'}
            request = self.factory.post('/pygments', data=form_data)
            view = views.PygmentsRoot.as_view()
            response = view(request)
            locations.append(response.items()[2][1])
            import time
            time.sleep(.1)
        request = self.factory.get('/pygments')
        view = views.PygmentsRoot.as_view()
        response = view(request)
        response_locations = json.loads(response.content)
        self.assertEquals(locations, response_locations)
        
        

