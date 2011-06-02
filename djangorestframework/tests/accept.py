from django.test import TestCase
from djangorestframework.compat import RequestFactory
from djangorestframework.views import View


# See: http://www.useragentstring.com/
MSIE_9_USER_AGENT = 'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))'
MSIE_8_USER_AGENT = 'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.2; Trident/4.0; Media Center PC 4.0; SLCC1; .NET CLR 3.0.04320)'
MSIE_7_USER_AGENT = 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)'
FIREFOX_4_0_USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.3) Gecko/20100401 Firefox/4.0 (.NET CLR 3.5.30729)'
CHROME_11_0_USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.655.0 Safari/534.17'
SAFARI_5_0_USER_AGENT = 'Mozilla/5.0 (X11; U; Linux x86_64; en-ca) AppleWebKit/531.2+ (KHTML, like Gecko) Version/5.0 Safari/531.2+'
OPERA_11_0_MSIE_USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; X11; Linux x86_64; pl) Opera 11.00'
OPERA_11_0_OPERA_USER_AGENT = 'Opera/9.80 (X11; Linux x86_64; U; pl) Presto/2.7.62 Version/11.00'

class UserAgentMungingTest(TestCase):
    """We need to fake up the accept headers when we deal with MSIE.  Blergh.
    http://www.gethifi.com/blog/browser-rest-http-accept-headers"""

    def setUp(self):

        class MockView(View):
            permissions = ()

            def get(self, request):
                return {'a':1, 'b':2, 'c':3}

        self.req = RequestFactory()
        self.MockView = MockView
        self.view = MockView.as_view()

    def test_munge_msie_accept_header(self):
        """Send MSIE user agent strings and ensure that we get an HTML response,
        even if we set a */* accept header."""
        for user_agent in (MSIE_9_USER_AGENT,
                           MSIE_8_USER_AGENT,
                           MSIE_7_USER_AGENT):
            req = self.req.get('/', HTTP_ACCEPT='*/*', HTTP_USER_AGENT=user_agent)
            resp = self.view(req)
            self.assertEqual(resp['Content-Type'], 'text/html')

    def test_dont_rewrite_msie_accept_header(self):
        """Turn off _IGNORE_IE_ACCEPT_HEADER, send MSIE user agent strings and ensure
        that we get a JSON response if we set a */* accept header."""
        view = self.MockView.as_view(_IGNORE_IE_ACCEPT_HEADER=False)

        for user_agent in (MSIE_9_USER_AGENT,
                           MSIE_8_USER_AGENT,
                           MSIE_7_USER_AGENT):
            req = self.req.get('/', HTTP_ACCEPT='*/*', HTTP_USER_AGENT=user_agent)
            resp = view(req)
            self.assertEqual(resp['Content-Type'], 'application/json')
    
    def test_dont_munge_nice_browsers_accept_header(self):
        """Send Non-MSIE user agent strings and ensure that we get a JSON response,
        if we set a */* Accept header.  (Other browsers will correctly set the Accept header)"""
        for user_agent in (FIREFOX_4_0_USER_AGENT,
                           CHROME_11_0_USER_AGENT,
                           SAFARI_5_0_USER_AGENT,
                           OPERA_11_0_MSIE_USER_AGENT,
                           OPERA_11_0_OPERA_USER_AGENT):
            req = self.req.get('/', HTTP_ACCEPT='*/*', HTTP_USER_AGENT=user_agent)
            resp = self.view(req)
            self.assertEqual(resp['Content-Type'], 'application/json')




