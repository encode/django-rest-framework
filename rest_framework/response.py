import re
from http.client import responses
from django.template.response import SimpleTemplateResponse
from rest_framework.serializers import Serializer
from rest_framework.renderers import JSONRenderer
from rest_framework import status

# Function to convert snake_case string to camelCase
def camel_case(snake_str):
    components = snake_str.split('_')  # Split the string by underscores
    return components[0] + ''.join(x.title() for x in components[1:])  # Join components into camelCase

# Function to recursively convert all dictionary keys in nested structures from snake_case to camelCase
def convert_keys_to_camel_case(data):
    if isinstance(data, dict):
        # If it's a dictionary, convert each key recursively
        return {camel_case(key): convert_keys_to_camel_case(value) for key, value in data.items()}
    elif isinstance(data, list):
        # If it's a list, apply the conversion to each item
        return [convert_keys_to_camel_case(item) for item in data]
    else:
        # If it's neither a dictionary nor a list, return the value as is
        return data

# Custom response class that extends SimpleTemplateResponse for custom formatting
class Response(SimpleTemplateResponse):

    def __init__(self, data=None, status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None,
                 renderer=JSONRenderer(), accepted_media_type='application/json', request=None):
        # Initialize the parent class
        super().__init__(None, status=status)

        # If data is an instance of Serializer, raise an error as it should be serialized first
        if isinstance(data, Serializer):
            msg = (
                'You passed a Serializer instance as data, but '
                'probably meant to pass serialized `.data` or '
                '`.error`. representation.'
            )
            raise AssertionError(msg)

        # Initialize other attributes
        self.data = data
        self.template_name = template_name
        self.exception = exception
        self.content_type = content_type

        # Set the renderer (default is JSONRenderer) and media type (default is JSON)
        self.accepted_renderer = renderer
        self.accepted_media_type = accepted_media_type

        # Store the request object for rendering context
        self.renderer_context = {
            'request': request
        }

        # Add any custom headers if provided
        if headers:
            for name, value in headers.items():
                self[name] = value

    # For Python 3.7+, this allows you to treat CustomResponse as a generic class
    def __class_getitem__(cls, *args, **kwargs):
        return cls

    # Property that renders the response content
    @property
    def rendered_content(self):
        # Get the renderer, media type, and context from the response
        renderer = self.accepted_renderer
        accepted_media_type = self.accepted_media_type
        context = self.renderer_context

        # Assertions to ensure required settings are provided
        assert renderer, ".accepted_renderer not set on Response"
        assert accepted_media_type, ".accepted_media_type not set on Response"
        assert context is not None, ".renderer_context not set on Response"
        context['response'] = self  # Add the current response to the context

        # Determine content type and charset
        media_type = renderer.media_type
        charset = renderer.charset
        content_type = self.content_type

        if content_type is None and charset is not None:
            content_type = "{}; charset={}".format(media_type, charset)
        elif content_type is None:
            content_type = media_type
        self['Content-Type'] = content_type  # Set the content type header

        # Render the response data
        ret = renderer.render(self.data, accepted_media_type, context)

        # Get the status code
        status_code = self.status_code

        # Map status codes to status messages
        code_to_msg = {
            status.HTTP_200_OK: "success",
            status.HTTP_202_ACCEPTED: "accepted",
            status.HTTP_201_CREATED: "created",
            status.HTTP_204_NO_CONTENT: "no_content",
            status.HTTP_400_BAD_REQUEST: "validation_error",
            status.HTTP_401_UNAUTHORIZED: "unauthorized",
            status.HTTP_403_FORBIDDEN: "forbidden",
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_406_NOT_ACCEPTABLE: "not_acceptable",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "server_error",
        }

        # Get the message corresponding to the status code
        status_message = code_to_msg.get(status_code, "unknown_error")

        # Create the final structured response
        structured_response = {
            "status": status_message,
            "code": status_code,
            "data": convert_keys_to_camel_case(self.data.get("data", {})),
            "message": self.data.get("message", ""),
        }

        # If the renderer returns a string, return the rendered JSON response
        if isinstance(ret, str):
            assert charset, (
                'renderer returned unicode, and did not specify '
                'a charset value.'
            )
            return JSONRenderer().render(structured_response)

        # If no content was rendered, remove the content type header
        if not ret:
            del self['Content-Type']

        return JSONRenderer().render(structured_response)

    # Property to get the status text corresponding to the status code
    @property
    def status_text(self):
        return responses.get(self.status_code, '')

    # Override __getstate__ to remove non-essential state info
    def __getstate__(self):
        state = super().__getstate__()
        for key in (
            'accepted_renderer', 'renderer_context', 'resolver_match',
            'client', 'request', 'json', 'wsgi_request'
        ):
            if key in state:
                del state[key]
        state['_closable_objects'] = []  # Clear closable objects to avoid issues
        return state
