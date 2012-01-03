import time

from django.conf.urls.defaults import patterns, url, include
from django.contrib.auth.models import User
from django.test import Client, TestCase

from djangorestframework.views import View

# Since oauth2 / django-oauth-plus are optional dependancies, we don't want to
# always run these tests.

# Unfortunatly we can't skip tests easily until 2.7, se we'll just do this for now.
try:
    import oauth2 as oauth
    from oauth_provider.decorators import oauth_required
    from oauth_provider.models import Resource, Consumer, Token

except ImportError:
    pass

else:
    # Alrighty, we're good to go here.
    class ClientView(View):
        def get(self, request):
            return {'resource': 'Protected!'}

    urlpatterns = patterns('',
        url(r'^$', oauth_required(ClientView.as_view())),
        url(r'^oauth/', include('oauth_provider.urls')),
        url(r'^accounts/login/$', 'djangorestframework.utils.staticviews.api_login'),
    )


    class OAuthTests(TestCase):
        """
        OAuth authentication:
        * the user would like to access his API data from a third-party website
        * the third-party website proposes a link to get that API data
        * the user is redirected to the API and must log in if not authenticated
        * the API displays a webpage to confirm that the user trusts the third-party website
        * if confirmed, the user is redirected to the third-party website through the callback view
        * the third-party website is able to retrieve data from the API
        """
        urls = 'djangorestframework.tests.oauthentication'

        def setUp(self):
            self.client = Client()
            self.username = 'john'
            self.email = 'lennon@thebeatles.com'
            self.password = 'password'
            self.user = User.objects.create_user(self.username, self.email, self.password)

            # OAuth requirements
            self.resource = Resource(name='data', url='/')
            self.resource.save()
            self.CONSUMER_KEY = 'dpf43f3p2l4k3l03'
            self.CONSUMER_SECRET = 'kd94hf93k423kf44'
            self.consumer = Consumer(key=self.CONSUMER_KEY, secret=self.CONSUMER_SECRET,
                                name='api.example.com', user=self.user)
            self.consumer.save()

        def test_oauth_invalid_and_anonymous_access(self):
            """
            Verify that the resource is protected and the OAuth authorization view
            require the user to be logged in.
            """
            response = self.client.get('/')
            self.assertEqual(response.content, 'Invalid request parameters.')
            self.assertEqual(response.status_code, 401)
            response = self.client.get('/oauth/authorize/', follow=True)
            self.assertRedirects(response, '/accounts/login/?next=/oauth/authorize/')

        def test_oauth_authorize_access(self):
            """
            Verify that once logged in, the user can access the authorization page
            but can't display the page because the request token is not specified.
            """
            self.client.login(username=self.username, password=self.password)
            response = self.client.get('/oauth/authorize/', follow=True)
            self.assertEqual(response.content, 'No request token specified.')

        def _create_request_token_parameters(self):
            """
            A shortcut to create request's token parameters.
            """
            return {
                'oauth_consumer_key': self.CONSUMER_KEY,
                'oauth_signature_method': 'PLAINTEXT',
                'oauth_signature': '%s&' % self.CONSUMER_SECRET,
                'oauth_timestamp': str(int(time.time())),
                'oauth_nonce': 'requestnonce',
                'oauth_version': '1.0',
                'oauth_callback': 'http://api.example.com/request_token_ready',
                'scope': 'data',
            }

        def test_oauth_request_token_retrieval(self):
            """
            Verify that the request token can be retrieved by the server.
            """
            response = self.client.get("/oauth/request_token/",
                                        self._create_request_token_parameters())
            self.assertEqual(response.status_code, 200)
            token = list(Token.objects.all())[-1]
            self.failIf(token.key not in response.content)
            self.failIf(token.secret not in response.content)

        def test_oauth_user_request_authorization(self):
            """
            Verify that the user can access the authorization page once logged in
            and the request token has been retrieved.
            """
            # Setup
            response = self.client.get("/oauth/request_token/",
                                        self._create_request_token_parameters())
            token = list(Token.objects.all())[-1]

            # Starting the test here
            self.client.login(username=self.username, password=self.password)
            parameters = {'oauth_token': token.key,}
            response = self.client.get("/oauth/authorize/", parameters)
            self.assertEqual(response.status_code, 200)
            self.failIf(not response.content.startswith('Fake authorize view for api.example.com with params: oauth_token='))
            self.assertEqual(token.is_approved, 0)
            parameters['authorize_access'] = 1 # fake authorization by the user
            response = self.client.post("/oauth/authorize/", parameters)
            self.assertEqual(response.status_code, 302)
            self.failIf(not response['Location'].startswith('http://api.example.com/request_token_ready?oauth_verifier='))
            token = Token.objects.get(key=token.key)
            self.failIf(token.key not in response['Location'])
            self.assertEqual(token.is_approved, 1)

        def _create_access_token_parameters(self, token):
            """
            A shortcut to create access' token parameters.
            """
            return {
                'oauth_consumer_key': self.CONSUMER_KEY,
                'oauth_token': token.key,
                'oauth_signature_method': 'PLAINTEXT',
                'oauth_signature': '%s&%s' % (self.CONSUMER_SECRET, token.secret),
                'oauth_timestamp': str(int(time.time())),
                'oauth_nonce': 'accessnonce',
                'oauth_version': '1.0',
                'oauth_verifier': token.verifier,
                'scope': 'data',
            }

        def test_oauth_access_token_retrieval(self):
            """
            Verify that the request token can be retrieved by the server.
            """
            # Setup
            response = self.client.get("/oauth/request_token/",
                                        self._create_request_token_parameters())
            token = list(Token.objects.all())[-1]
            self.client.login(username=self.username, password=self.password)
            parameters = {'oauth_token': token.key,}
            response = self.client.get("/oauth/authorize/", parameters)
            parameters['authorize_access'] = 1 # fake authorization by the user
            response = self.client.post("/oauth/authorize/", parameters)
            token = Token.objects.get(key=token.key)

            # Starting the test here
            response = self.client.get("/oauth/access_token/", self._create_access_token_parameters(token))
            self.assertEqual(response.status_code, 200)
            self.failIf(not response.content.startswith('oauth_token_secret='))
            access_token = list(Token.objects.filter(token_type=Token.ACCESS))[-1]
            self.failIf(access_token.key not in response.content)
            self.failIf(access_token.secret not in response.content)
            self.assertEqual(access_token.user.username, 'john')

        def _create_access_parameters(self, access_token):
            """
            A shortcut to create access' parameters.
            """
            parameters = {
                'oauth_consumer_key': self.CONSUMER_KEY,
                'oauth_token': access_token.key,
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': str(int(time.time())),
                'oauth_nonce': 'accessresourcenonce',
                'oauth_version': '1.0',
            }
            oauth_request = oauth.Request.from_token_and_callback(access_token,
                http_url='http://testserver/', parameters=parameters)
            signature_method = oauth.SignatureMethod_HMAC_SHA1()
            signature = signature_method.sign(oauth_request, self.consumer, access_token)
            parameters['oauth_signature'] = signature
            return parameters

        def test_oauth_protected_resource_access(self):
            """
            Verify that the request token can be retrieved by the server.
            """
            # Setup
            response = self.client.get("/oauth/request_token/",
                                        self._create_request_token_parameters())
            token = list(Token.objects.all())[-1]
            self.client.login(username=self.username, password=self.password)
            parameters = {'oauth_token': token.key,}
            response = self.client.get("/oauth/authorize/", parameters)
            parameters['authorize_access'] = 1 # fake authorization by the user
            response = self.client.post("/oauth/authorize/", parameters)
            token = Token.objects.get(key=token.key)
            response = self.client.get("/oauth/access_token/", self._create_access_token_parameters(token))
            access_token = list(Token.objects.filter(token_type=Token.ACCESS))[-1]

            # Starting the test here
            response = self.client.get("/", self._create_access_token_parameters(access_token))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, '{"resource": "Protected!"}')
