from __future__ import unicode_literals
from rest_framework import exceptions, metadata, serializers, status, views, versioning
from rest_framework.request import Request
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.test import APIRequestFactory

request = Request(APIRequestFactory().options('/'))


class TestMetadata:
    def test_metadata(self):
        """
        OPTIONS requests to views should return a valid 200 response.
        """
        class ExampleView(views.APIView):
            """Example view."""
            pass

        view = ExampleView.as_view()
        response = view(request=request)
        expected = {
            'name': 'Example',
            'description': 'Example view.',
            'renders': [
                'application/json',
                'text/html'
            ],
            'parses': [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ]
        }
        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    def test_none_metadata(self):
        """
        OPTIONS requests to views where `metadata_class = None` should raise
        a MethodNotAllowed exception, which will result in an HTTP 405 response.
        """
        class ExampleView(views.APIView):
            metadata_class = None

        view = ExampleView.as_view()
        response = view(request=request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == {'detail': 'Method "OPTIONS" not allowed.'}

    def test_actions(self):
        """
        On generic views OPTIONS should return an 'actions' key with metadata
        on the fields that may be supplied to PUT and POST requests.
        """
        class ExampleSerializer(serializers.Serializer):
            choice_field = serializers.ChoiceField(['red', 'green', 'blue'])
            integer_field = serializers.IntegerField(
                min_value=1, max_value=1000
            )
            char_field = serializers.CharField(
                required=False, min_length=3, max_length=40
            )

        class ExampleView(views.APIView):
            """Example view."""
            def post(self, request):
                pass

            def get_serializer(self):
                return ExampleSerializer()

        view = ExampleView.as_view()
        response = view(request=request)
        expected = {
            'name': 'Example',
            'description': 'Example view.',
            'renders': [
                'application/json',
                'text/html'
            ],
            'parses': [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ],
            'actions': {
                'POST': {
                    'choice_field': {
                        'type': 'choice',
                        'required': True,
                        'read_only': False,
                        'label': 'Choice field',
                        'choices': [
                            {'display_name': 'red', 'value': 'red'},
                            {'display_name': 'green', 'value': 'green'},
                            {'display_name': 'blue', 'value': 'blue'}
                        ]
                    },
                    'integer_field': {
                        'type': 'integer',
                        'required': True,
                        'read_only': False,
                        'label': 'Integer field',
                        'min_value': 1,
                        'max_value': 1000,

                    },
                    'char_field': {
                        'type': 'string',
                        'required': False,
                        'read_only': False,
                        'label': 'Char field',
                        'min_length': 3,
                        'max_length': 40
                    }
                }
            }
        }
        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    def test_global_permissions(self):
        """
        If a user does not have global permissions on an action, then any
        metadata associated with it should not be included in OPTION responses.
        """
        class ExampleSerializer(serializers.Serializer):
            choice_field = serializers.ChoiceField(['red', 'green', 'blue'])
            integer_field = serializers.IntegerField(max_value=10)
            char_field = serializers.CharField(required=False)

        class ExampleView(views.APIView):
            """Example view."""
            def post(self, request):
                pass

            def put(self, request):
                pass

            def get_serializer(self):
                return ExampleSerializer()

            def check_permissions(self, request):
                if request.method == 'POST':
                    raise exceptions.PermissionDenied()

        view = ExampleView.as_view()
        response = view(request=request)
        assert response.status_code == status.HTTP_200_OK
        assert list(response.data['actions'].keys()) == ['PUT']

    def test_object_permissions(self):
        """
        If a user does not have object permissions on an action, then any
        metadata associated with it should not be included in OPTION responses.
        """
        class ExampleSerializer(serializers.Serializer):
            choice_field = serializers.ChoiceField(['red', 'green', 'blue'])
            integer_field = serializers.IntegerField(max_value=10)
            char_field = serializers.CharField(required=False)

        class ExampleView(views.APIView):
            """Example view."""
            def post(self, request):
                pass

            def put(self, request):
                pass

            def get_serializer(self):
                return ExampleSerializer()

            def get_object(self):
                if self.request.method == 'PUT':
                    raise exceptions.PermissionDenied()

        view = ExampleView.as_view()
        response = view(request=request)
        assert response.status_code == status.HTTP_200_OK
        assert list(response.data['actions'].keys()) == ['POST']

    def test_bug_2455_clone_request(self):
        class ExampleView(views.APIView):
            renderer_classes = (BrowsableAPIRenderer,)

            def post(self, request):
                pass

            def get_serializer(self):
                assert hasattr(self.request, 'version')
                return serializers.Serializer()

        view = ExampleView.as_view()
        view(request=request)

    def test_bug_2477_clone_request(self):
        class ExampleView(views.APIView):
            renderer_classes = (BrowsableAPIRenderer,)

            def post(self, request):
                pass

            def get_serializer(self):
                assert hasattr(self.request, 'versioning_scheme')
                return serializers.Serializer()

        scheme = versioning.QueryParameterVersioning
        view = ExampleView.as_view(versioning_class=scheme)
        view(request=request)

    def test_null_boolean_field_info_type(self):
        options = metadata.SimpleMetadata()
        field_info = options.get_field_info(serializers.NullBooleanField())
        assert field_info['type'] == 'boolean'
