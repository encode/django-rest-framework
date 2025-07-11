from coreapi.utils import domain_matches
from requests.auth import AuthBase, HTTPBasicAuth


class BasicAuthentication(HTTPBasicAuth):
    allow_cookies = False

    def __init__(self, username, password, domain=None):
        self.domain = domain
        super(BasicAuthentication, self).__init__(username, password)

    def __call__(self, request):
        if not domain_matches(request, self.domain):
            return request

        return super(BasicAuthentication, self).__call__(request)


class TokenAuthentication(AuthBase):
    allow_cookies = False
    scheme = 'Bearer'

    def __init__(self, token, scheme=None, domain=None):
        """
        * Use an unauthenticated client, and make a request to obtain a token.
        * Create an authenticated client using eg. `TokenAuthentication(token="<token>")`
        """
        self.token = token
        self.domain = domain
        if scheme is not None:
            self.scheme = scheme

    def __call__(self, request):
        if not domain_matches(request, self.domain):
            return request

        request.headers['Authorization'] = '%s %s' % (self.scheme, self.token)
        return request


class SessionAuthentication(AuthBase):
    """
    Enables session based login.

    * Make an initial request to obtain a CSRF token.
    * Make a login request.
    """
    allow_cookies = True
    safe_methods = ('GET', 'HEAD', 'OPTIONS', 'TRACE')

    def __init__(self, csrf_cookie_name=None, csrf_header_name=None, domain=None):
        self.csrf_cookie_name = csrf_cookie_name
        self.csrf_header_name = csrf_header_name
        self.csrf_token = None
        self.domain = domain

    def store_csrf_token(self, response, **kwargs):
        if self.csrf_cookie_name in response.cookies:
            self.csrf_token = response.cookies[self.csrf_cookie_name]

    def __call__(self, request):
        if not domain_matches(request, self.domain):
            return request

        if self.csrf_token and self.csrf_header_name is not None and (request.method not in self.safe_methods):
            request.headers[self.csrf_header_name] = self.csrf_token
        if self.csrf_cookie_name is not None:
            request.register_hook('response', self.store_csrf_token)
        return request
