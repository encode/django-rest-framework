<a class="github" href="parsers.py"></a>

# Parsers

> Machine interacting web services tend to use more
structured formats for sending data than form-encoded, since they're
sending more complex data than simple forms
>
> &mdash; Malcom Tredinnick, [Django developers group][cite]

REST framework includes a number of built in Parser classes, that allow you to accept requests with various media types.  There is also support for defining your own custom parsers, which gives you the flexibility to design the media types that your API accepts.

## How the parser is determined

The set of valid parsers for a view is always defined as a list of classes.  When either `request.DATA` or `request.FILES` is accessed, REST framework will examine the `Content-Type` header on the incoming request, and determine which parser to use to parse the request content.

## Setting the parsers

The default set of parsers may be set globally, using the `DEFAULT_PARSER_CLASSES` setting.  For example, the following settings would allow requests with `YAML` content.

    REST_FRAMEWORK = {
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework.parsers.YAMLParser',
        )
    }

You can also set the renderers used for an individual view, using the `APIView` class based views.

    class ExampleView(APIView):
        """
        A view that can accept POST requests with YAML content.
        """
        parser_classes = (YAMLParser,)

        def post(self, request, format=None):
            return Response({'received data': request.DATA})

Or, if you're using the `@api_view` decorator with function based views.

    @api_view(['POST'])
    @parser_classes((YAMLParser,))
    def example_view(request, format=None):
        """
        A view that can accept POST requests with YAML content.
        """
        return Response({'received data': request.DATA})

---

# API Reference

## JSONParser

Parses `JSON` request content.

**.media_type**: `application/json`

## YAMLParser

Parses `YAML` request content.

**.media_type**: `application/yaml`

## XMLParser

Parses REST framework's default style of `XML` request content.

Note that the `XML` markup language is typically used as the base language for more strictly defined domain-specific languages, such as `RSS`, `Atom`, and `XHTML`.

If you are considering using `XML` for your API, you may want to consider implementing a custom renderer and parser for your specific requirements, and using an existing domain-specific media-type, or creating your own custom XML-based media-type.

**.media_type**: `application/xml`

## FormParser

Parses HTML form content.  `request.DATA` will be populated with a `QueryDict` of data, `request.FILES` will be populated with an empty `QueryDict` of data.

You will typically want to use both `FormParser` and `MultiPartParser` together in order to fully support HTML form data.

**.media_type**: `application/x-www-form-urlencoded`

## MultiPartParser

Parses multipart HTML form content, which supports file uploads.  Both `request.DATA` and `request.FILES` will be populated with a `QueryDict`.

You will typically want to use both `FormParser` and `MultiPartParser` together in order to fully support HTML form data.

**.media_type**: `multipart/form-data`

---

# Custom parsers

To implement a custom parser, you should override `BaseParser`, set the `.media_type` property, and implement the `.parse(self, stream, media_type, parser_context)` method.

The method should return the data that will be used to populate the `request.DATA` property.

The arguments passed to `.parse()` are:

### stream

A stream-like object representing the body of the request.

### media_type

Optional.  If provided, this is the media type of the incoming request content.

Depending on the request's `Content-Type:` header, this may be more specific than the renderer's `media_type` attribute, and may include media type parameters.  For example `"text/plain; charset=utf-8"`.

### parser_context

Optional.  If supplied, this argument will be a dictionary containing any additional context that may be required to parse the request content.

By default this will include the following keys: `view`, `request`, `args`, `kwargs`.

## Example

The following is an example plaintext parser that will populate the `request.DATA` property with a string representing the body of the request. 

    class PlainTextParser(BaseParser):
    """
    Plain text parser.
    """

    media_type = 'text/plain'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Simply return a string representing the body of the request.
        """
        return stream.read()

## Uploading file content

If your custom parser needs to support file uploads, you may return a `DataAndFiles` object from the `.parse()` method.  `DataAndFiles` should be instantiated with two arguments.  The first argument will be used to populate the `request.DATA` property, and the second argument will be used to populate the `request.FILES` property.

For example:

    class SimpleFileUploadParser(BaseParser):
        """
        A naive raw file upload parser.
        """
        media_type = '*/*'  # Accept anything

        def parse(self, stream, media_type=None, parser_context=None):
            content = stream.read()
            name = 'example.dat'
            content_type = 'application/octet-stream'
            size = len(content)
            charset = 'utf-8'

            # Write a temporary file based on the request content
            temp = tempfile.NamedTemporaryFile(delete=False)
            temp.write(content)
            uploaded = UploadedFile(temp, name, content_type, size, charset)

            # Return the uploaded file
            data = {}
            files = {name: uploaded}
            return DataAndFiles(data, files)

[cite]: https://groups.google.com/d/topic/django-developers/dxI4qVzrBY4/discussion
