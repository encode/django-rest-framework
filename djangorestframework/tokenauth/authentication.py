from djangorestframework.authentication import BaseAuthentication
from .models import BasicToken

class TokenAuthentication(BaseAuthentication):
    """
    Use a token model for authentication.

    A custom token model may be used here, but must have the following minimum
    properties:

    * key -- The string identifying the token
    * user -- The user to which the token belongs
    * revoked -- The status of the token

    The BaseToken class is available as an abstract model to be derived from.

    The token key should be passed in as a string to the "Authorization" HTTP
    header.  For example:

        Authorization: Token 0123456789abcdef0123456789abcdef

    """
    model = BasicToken

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '').strip().split()
        if len(auth) == 2 and auth[0].lower() == "token":
            key = auth[1]

            try:
                 token = self.model.objects.get(key=key)
            except self.model.DoesNotExist:
                 return None

            if token.user.is_active and not token.revoked:
                return (token.user, token)
