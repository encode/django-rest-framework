<a class="github" href="test.py"></a>

# Testing

> Code without tests is broken as designed
>
> &mdash; [Jacob Kaplan-Moss][cite]

REST framework includes a few helper classes that extend Django's existing test framework, and improve support for making API requests.

# APIRequestFactory

Extends Django's existing `RequestFactory`.

**TODO**: Document making requests.  Note difference on form PUT requests.  Document configuration.

# APIClient

Extends Django's existing `Client`.

### .login(**kwargs)

The `login` method functions exactly as it does with Django's regular `Client` class.  This allows you to authenticate requests against any views which include `SessionAuthentication`.

    # Make all requests in the context of a logged in session.
    >>> client = APIClient()
    >>> client.login(username='lauren', password='secret')

To logout, call the `logout` method as usual.

    # Log out
    >>> client.logout()

The `login` method is appropriate for testing APIs that use session authentication, for example web sites which include AJAX interaction with the API.

### .credentials(**kwargs)

The `credentials` method can be used to set headers that will then be included on all subsequent requests by the test client.

    # Include an appropriate `Authorization:` header on all requests.
    >>> token = Token.objects.get(username='lauren')
    >>> client = APIClient()
    >>> client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

Note that calling `credentials` a second time overwrites any existing credentials.  You can unset any existing credentials by calling the method with no arguments.

    # Stop including any credentials
    >>> client.credentials()

The `credentials` method is appropriate for testing APIs that require authentication headers, such as basic authentication, OAuth1a and OAuth2 authentication, and simple token authentication schemes.

### .force_authenticate(user=None, token=None)

Sometimes you may want to bypass authentication, and simple force all requests by the test client to be automatically treated as authenticated.

This can be a useful shortcut if you're testing the API but don't want to have to construct valid authentication credentials in order to make test requests.

    >>> user = User.objects.get(username='lauren')
    >>> client = APIClient()
    >>> client.force_authenticate(user=user)

To unauthenticate subsequant requests, call `force_authenticate` setting the user and/or token to `None`.

    >>> client.force_authenticate(user=None) 

### Making requests

**TODO**: Document requests similarly to `APIRequestFactory`

# Testing responses

### Using request.data

When checking the validity of test responses it's often more convenient to inspect the data that the response was created with, rather than inspecting the fully rendered response.

For example, it's easier to inspect `request.data`:

    response = self.client.get('/users/4/')
    self.assertEqual(response.data, {'id': 4, 'username': 'lauren'})

Instead of inspecting the result of parsing `request.content`:

    response = self.client.get('/users/4/')
    self.assertEqual(json.loads(response.content), {'id': 4, 'username': 'lauren'})

### Rendering responses

If you're testing views directly using `APIRequestFactory`, the responses that are returned will not yet be rendered, as rendering of template responses is performed by Django's internal request-response cycle.  In order to access `response.content`, you'll first need to render the response.

    view = UserDetail.as_view()
    request = factory.get('/users/4')
    response = view(request, pk='4')
    response.render()  # Cannot access `response.content` without this.
    self.assertEqual(response.content, '{"username": "lauren", "id": 4}')
    

[cite]: http://jacobian.org/writing/django-apps-with-buildout/#s-create-a-test-wrapper