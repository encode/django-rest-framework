from __future__ import unicode_literals
from django.db import models
from django.test import TestCase
from rest_framework import generics, serializers, status
from rest_framework.tests.utils import RequestFactory
from rest_framework.tests.models import BasicModel, Comment, SlugBasedModel
from rest_framework.compat import six
import json

factory = RequestFactory()


class RootView(generics.ListCreateAPIView):
    """
    Example description for OPTIONS.
    """
    model = BasicModel


class InstanceView(generics.RetrieveUpdateDestroyAPIView):
    """
    Example description for OPTIONS.
    """
    model = BasicModel


class SlugSerializer(serializers.ModelSerializer):
    slug = serializers.Field()  # read only

    class Meta:
        model = SlugBasedModel
        exclude = ('id',)


class SlugBasedInstanceView(InstanceView):
    """
    A model with a slug-field.
    """
    model = SlugBasedModel
    serializer_class = SlugSerializer


class TestRootView(TestCase):
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
        self.view = RootView.as_view()

    def test_get_root_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

    def test_post_root_view(self):
        """
        POST requests to ListCreateAPIView should create a new object.
        """
        content = {'text': 'foobar'}
        request = factory.post('/', json.dumps(content),
                               content_type='application/json')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'id': 4, 'text': 'foobar'})
        created = self.objects.get(id=4)
        self.assertEqual(created.text, 'foobar')

    def test_put_root_view(self):
        """
        PUT requests to ListCreateAPIView should not be allowed
        """
        content = {'text': 'foobar'}
        request = factory.put('/', json.dumps(content),
                              content_type='application/json')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": "Method 'PUT' not allowed."})

    def test_delete_root_view(self):
        """
        DELETE requests to ListCreateAPIView should not be allowed
        """
        request = factory.delete('/')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": "Method 'DELETE' not allowed."})

    def test_options_root_view(self):
        """
        OPTIONS requests to ListCreateAPIView should return metadata
        """
        request = factory.options('/')
        response = self.view(request).render()
        expected = {
            'parses': [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ],
            'renders': [
                'application/json',
                'text/html'
            ],
            'name': 'Root',
            'description': 'Example description for OPTIONS.'
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_post_cannot_set_id(self):
        """
        POST requests to create a new object should not be able to set the id.
        """
        content = {'id': 999, 'text': 'foobar'}
        request = factory.post('/', json.dumps(content),
                               content_type='application/json')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'id': 4, 'text': 'foobar'})
        created = self.objects.get(id=4)
        self.assertEqual(created.text, 'foobar')


class TestInstanceView(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel intances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]
        self.view = InstanceView.as_view()
        self.slug_based_view = SlugBasedInstanceView.as_view()

    def test_get_instance_view(self):
        """
        GET requests to RetrieveUpdateDestroyAPIView should return a single object.
        """
        request = factory.get('/1')
        response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data[0])

    def test_post_instance_view(self):
        """
        POST requests to RetrieveUpdateDestroyAPIView should not be allowed
        """
        content = {'text': 'foobar'}
        request = factory.post('/', json.dumps(content),
                               content_type='application/json')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": "Method 'POST' not allowed."})

    def test_put_instance_view(self):
        """
        PUT requests to RetrieveUpdateDestroyAPIView should update an object.
        """
        content = {'text': 'foobar'}
        request = factory.put('/1', json.dumps(content),
                              content_type='application/json')
        response = self.view(request, pk='1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'id': 1, 'text': 'foobar'})
        updated = self.objects.get(id=1)
        self.assertEqual(updated.text, 'foobar')

    def test_patch_instance_view(self):
        """
        PATCH requests to RetrieveUpdateDestroyAPIView should update an object.
        """
        content = {'text': 'foobar'}
        request = factory.patch('/1', json.dumps(content),
                              content_type='application/json')

        response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'id': 1, 'text': 'foobar'})
        updated = self.objects.get(id=1)
        self.assertEqual(updated.text, 'foobar')

    def test_delete_instance_view(self):
        """
        DELETE requests to RetrieveUpdateDestroyAPIView should delete an object.
        """
        request = factory.delete('/1')
        response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, six.b(''))
        ids = [obj.id for obj in self.objects.all()]
        self.assertEqual(ids, [2, 3])

    def test_options_instance_view(self):
        """
        OPTIONS requests to RetrieveUpdateDestroyAPIView should return metadata
        """
        request = factory.options('/')
        response = self.view(request).render()
        expected = {
            'parses': [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ],
            'renders': [
                'application/json',
                'text/html'
            ],
            'name': 'Instance',
            'description': 'Example description for OPTIONS.'
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_put_cannot_set_id(self):
        """
        PUT requests to create a new object should not be able to set the id.
        """
        content = {'id': 999, 'text': 'foobar'}
        request = factory.put('/1', json.dumps(content),
                              content_type='application/json')
        response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'id': 1, 'text': 'foobar'})
        updated = self.objects.get(id=1)
        self.assertEqual(updated.text, 'foobar')

    def test_put_to_deleted_instance(self):
        """
        PUT requests to RetrieveUpdateDestroyAPIView should create an object
        if it does not currently exist.
        """
        self.objects.get(id=1).delete()
        content = {'text': 'foobar'}
        request = factory.put('/1', json.dumps(content),
                              content_type='application/json')
        response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'id': 1, 'text': 'foobar'})
        updated = self.objects.get(id=1)
        self.assertEqual(updated.text, 'foobar')

    def test_put_as_create_on_id_based_url(self):
        """
        PUT requests to RetrieveUpdateDestroyAPIView should create an object
        at the requested url if it doesn't exist.
        """
        content = {'text': 'foobar'}
        # pk fields can not be created on demand, only the database can set th pk for a new object
        request = factory.put('/5', json.dumps(content),
                              content_type='application/json')
        response = self.view(request, pk=5).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_obj = self.objects.get(pk=5)
        self.assertEqual(new_obj.text, 'foobar')

    def test_put_as_create_on_slug_based_url(self):
        """
        PUT requests to RetrieveUpdateDestroyAPIView should create an object
        at the requested url if possible, else return HTTP_403_FORBIDDEN error-response.
        """
        content = {'text': 'foobar'}
        request = factory.put('/test_slug', json.dumps(content),
                              content_type='application/json')
        response = self.slug_based_view(request, slug='test_slug').render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'slug': 'test_slug', 'text': 'foobar'})
        new_obj = SlugBasedModel.objects.get(slug='test_slug')
        self.assertEqual(new_obj.text, 'foobar')


# Regression test for #285

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        exclude = ('created',)


class CommentView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    model = Comment


class TestCreateModelWithAutoNowAddField(TestCase):
    def setUp(self):
        self.objects = Comment.objects
        self.view = CommentView.as_view()

    def test_create_model_with_auto_now_add_field(self):
        """
        Regression test for #285

        https://github.com/tomchristie/django-rest-framework/issues/285
        """
        content = {'email': 'foobar@example.com', 'content': 'foobar'}
        request = factory.post('/', json.dumps(content),
                               content_type='application/json')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = self.objects.get(id=1)
        self.assertEqual(created.content, 'foobar')


# Test for particularly ugly regression with m2m in browseable API
class ClassB(models.Model):
    name = models.CharField(max_length=255)


class ClassA(models.Model):
    name = models.CharField(max_length=255)
    childs = models.ManyToManyField(ClassB, blank=True, null=True)


class ClassASerializer(serializers.ModelSerializer):
    childs = serializers.PrimaryKeyRelatedField(many=True, source='childs')

    class Meta:
        model = ClassA


class ExampleView(generics.ListCreateAPIView):
    serializer_class = ClassASerializer
    model = ClassA


class TestM2MBrowseableAPI(TestCase):
    def test_m2m_in_browseable_api(self):
        """
        Test for particularly ugly regression with m2m in browseable API
        """
        request = factory.get('/', HTTP_ACCEPT='text/html')
        view = ExampleView().as_view()
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
