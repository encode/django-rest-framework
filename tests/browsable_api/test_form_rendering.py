from django.test import TestCase

from rest_framework import generics, renderers, serializers, status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from tests.models import BasicModel

factory = APIRequestFactory()


class BasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'


class ManyPostView(generics.GenericAPIView):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status.HTTP_200_OK)


class TestManyPostView(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel instances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]
        self.view = ManyPostView.as_view()

    def test_post_many_post_view(self):
        """
        POST request to a view that returns a list of objects should
        still successfully return the browsable API with a rendered form.

        Regression test for https://github.com/tomchristie/django-rest-framework/pull/3164
        """
        data = {}
        request = factory.post('/', data, format='json')
        with self.assertNumQueries(1):
            response = self.view(request).render()
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
