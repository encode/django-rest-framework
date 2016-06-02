from __future__ import unicode_literals

import pytest
from django.db import models
from django.shortcuts import get_object_or_404
from django.test import TestCase
from django.utils import six

from rest_framework import generics, renderers, serializers, status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from tests.models import (
    BasicModel, ForeignKeySource, ForeignKeyTarget, RESTFrameworkModel
)

factory = APIRequestFactory()


# Models
class SlugBasedModel(RESTFrameworkModel):
    text = models.CharField(max_length=100)
    slug = models.SlugField(max_length=32)


# Model for regression test for #285
class Comment(RESTFrameworkModel):
    email = models.EmailField()
    content = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)


# Serializers
class BasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'


class ForeignKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = '__all__'


class SlugSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField()

    class Meta:
        model = SlugBasedModel
        fields = ('text', 'slug')


# Views
class RootView(generics.ListCreateAPIView):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer


class InstanceView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BasicModel.objects.exclude(text='filtered out')
    serializer_class = BasicSerializer


class FKInstanceView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ForeignKeySource.objects.all()
    serializer_class = ForeignKeySerializer


class SlugBasedInstanceView(InstanceView):
    """
    A model with a slug-field.
    """
    queryset = SlugBasedModel.objects.all()
    serializer_class = SlugSerializer
    lookup_field = 'slug'


# Tests
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
        with self.assertNumQueries(1):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

    def test_post_root_view(self):
        """
        POST requests to ListCreateAPIView should create a new object.
        """
        data = {'text': 'foobar'}
        request = factory.post('/', data, format='json')
        with self.assertNumQueries(1):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'id': 4, 'text': 'foobar'})
        created = self.objects.get(id=4)
        self.assertEqual(created.text, 'foobar')

    def test_put_root_view(self):
        """
        PUT requests to ListCreateAPIView should not be allowed
        """
        data = {'text': 'foobar'}
        request = factory.put('/', data, format='json')
        with self.assertNumQueries(0):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": 'Method "PUT" not allowed.'})

    def test_delete_root_view(self):
        """
        DELETE requests to ListCreateAPIView should not be allowed
        """
        request = factory.delete('/')
        with self.assertNumQueries(0):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": 'Method "DELETE" not allowed.'})

    def test_post_cannot_set_id(self):
        """
        POST requests to create a new object should not be able to set the id.
        """
        data = {'id': 999, 'text': 'foobar'}
        request = factory.post('/', data, format='json')
        with self.assertNumQueries(1):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'id': 4, 'text': 'foobar'})
        created = self.objects.get(id=4)
        self.assertEqual(created.text, 'foobar')

    def test_post_error_root_view(self):
        """
        POST requests to ListCreateAPIView in HTML should include a form error.
        """
        data = {'text': 'foobar' * 100}
        request = factory.post('/', data, HTTP_ACCEPT='text/html')
        response = self.view(request).render()
        expected_error = '<span class="help-block">Ensure this field has no more than 100 characters.</span>'
        self.assertIn(expected_error, response.rendered_content.decode('utf-8'))


EXPECTED_QUERIES_FOR_PUT = 2


class TestInstanceView(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel instances.
        """
        items = ['foo', 'bar', 'baz', 'filtered out']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects.exclude(text='filtered out')
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
        with self.assertNumQueries(1):
            response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data[0])

    def test_post_instance_view(self):
        """
        POST requests to RetrieveUpdateDestroyAPIView should not be allowed
        """
        data = {'text': 'foobar'}
        request = factory.post('/', data, format='json')
        with self.assertNumQueries(0):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": 'Method "POST" not allowed.'})

    def test_put_instance_view(self):
        """
        PUT requests to RetrieveUpdateDestroyAPIView should update an object.
        """
        data = {'text': 'foobar'}
        request = factory.put('/1', data, format='json')
        with self.assertNumQueries(EXPECTED_QUERIES_FOR_PUT):
            response = self.view(request, pk='1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(dict(response.data), {'id': 1, 'text': 'foobar'})
        updated = self.objects.get(id=1)
        self.assertEqual(updated.text, 'foobar')

    def test_patch_instance_view(self):
        """
        PATCH requests to RetrieveUpdateDestroyAPIView should update an object.
        """
        data = {'text': 'foobar'}
        request = factory.patch('/1', data, format='json')

        with self.assertNumQueries(EXPECTED_QUERIES_FOR_PUT):
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
        with self.assertNumQueries(2):
            response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, six.b(''))
        ids = [obj.id for obj in self.objects.all()]
        self.assertEqual(ids, [2, 3])

    def test_get_instance_view_incorrect_arg(self):
        """
        GET requests with an incorrect pk type, should raise 404, not 500.
        Regression test for #890.
        """
        request = factory.get('/a')
        with self.assertNumQueries(0):
            response = self.view(request, pk='a').render()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_cannot_set_id(self):
        """
        PUT requests to create a new object should not be able to set the id.
        """
        data = {'id': 999, 'text': 'foobar'}
        request = factory.put('/1', data, format='json')
        with self.assertNumQueries(EXPECTED_QUERIES_FOR_PUT):
            response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'id': 1, 'text': 'foobar'})
        updated = self.objects.get(id=1)
        self.assertEqual(updated.text, 'foobar')

    def test_put_to_deleted_instance(self):
        """
        PUT requests to RetrieveUpdateDestroyAPIView should return 404 if
        an object does not currently exist.
        """
        self.objects.get(id=1).delete()
        data = {'text': 'foobar'}
        request = factory.put('/1', data, format='json')
        with self.assertNumQueries(1):
            response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_to_filtered_out_instance(self):
        """
        PUT requests to an URL of instance which is filtered out should not be
        able to create new objects.
        """
        data = {'text': 'foo'}
        filtered_out_pk = BasicModel.objects.filter(text='filtered out')[0].pk
        request = factory.put('/{0}'.format(filtered_out_pk), data, format='json')
        response = self.view(request, pk=filtered_out_pk).render()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_cannot_create_an_object(self):
        """
        PATCH requests should not be able to create objects.
        """
        data = {'text': 'foobar'}
        request = factory.patch('/999', data, format='json')
        with self.assertNumQueries(1):
            response = self.view(request, pk=999).render()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(self.objects.filter(id=999).exists())

    def test_put_error_instance_view(self):
        """
        Incorrect PUT requests in HTML should include a form error.
        """
        data = {'text': 'foobar' * 100}
        request = factory.put('/', data, HTTP_ACCEPT='text/html')
        response = self.view(request, pk=1).render()
        expected_error = '<span class="help-block">Ensure this field has no more than 100 characters.</span>'
        self.assertIn(expected_error, response.rendered_content.decode('utf-8'))


class TestFKInstanceView(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel instances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            t = ForeignKeyTarget(name=item)
            t.save()
            ForeignKeySource(name='source_' + item, target=t).save()

        self.objects = ForeignKeySource.objects
        self.data = [
            {'id': obj.id, 'name': obj.name}
            for obj in self.objects.all()
        ]
        self.view = FKInstanceView.as_view()


class TestOverriddenGetObject(TestCase):
    """
    Test cases for a RetrieveUpdateDestroyAPIView that does NOT use the
    queryset/model mechanism but instead overrides get_object()
    """

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

        class OverriddenGetObjectView(generics.RetrieveUpdateDestroyAPIView):
            """
            Example detail view for override of get_object().
            """
            serializer_class = BasicSerializer

            def get_object(self):
                pk = int(self.kwargs['pk'])
                return get_object_or_404(BasicModel.objects.all(), id=pk)

        self.view = OverriddenGetObjectView.as_view()

    def test_overridden_get_object_view(self):
        """
        GET requests to RetrieveUpdateDestroyAPIView should return a single object.
        """
        request = factory.get('/1')
        with self.assertNumQueries(1):
            response = self.view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data[0])


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
        data = {'email': 'foobar@example.com', 'content': 'foobar'}
        request = factory.post('/', data, format='json')
        response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = self.objects.get(id=1)
        self.assertEqual(created.content, 'foobar')


# Test for particularly ugly regression with m2m in browsable API
class ClassB(models.Model):
    name = models.CharField(max_length=255)


class ClassA(models.Model):
    name = models.CharField(max_length=255)
    children = models.ManyToManyField(ClassB, blank=True, null=True)


class ClassASerializer(serializers.ModelSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ClassB.objects.all()
    )

    class Meta:
        model = ClassA
        fields = '__all__'


class ExampleView(generics.ListCreateAPIView):
    serializer_class = ClassASerializer
    queryset = ClassA.objects.all()


class TestM2MBrowsableAPI(TestCase):
    def test_m2m_in_browsable_api(self):
        """
        Test for particularly ugly regression with m2m in browsable API
        """
        request = factory.get('/', HTTP_ACCEPT='text/html')
        view = ExampleView().as_view()
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class InclusiveFilterBackend(object):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(text='foo')


class ExclusiveFilterBackend(object):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(text='other')


class TwoFieldModel(models.Model):
    field_a = models.CharField(max_length=100)
    field_b = models.CharField(max_length=100)


class DynamicSerializerView(generics.ListCreateAPIView):
    queryset = TwoFieldModel.objects.all()
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            class DynamicSerializer(serializers.ModelSerializer):
                class Meta:
                    model = TwoFieldModel
                    fields = ('field_b',)
        else:
            class DynamicSerializer(serializers.ModelSerializer):
                class Meta:
                    model = TwoFieldModel
                    fields = '__all__'
        return DynamicSerializer


class TestFilterBackendAppliedToViews(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel instances to filter on.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]

    def test_get_root_view_filters_by_name_with_filter_backend(self):
        """
        GET requests to ListCreateAPIView should return filtered list.
        """
        root_view = RootView.as_view(filter_backends=(InclusiveFilterBackend,))
        request = factory.get('/')
        response = root_view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, [{'id': 1, 'text': 'foo'}])

    def test_get_root_view_filters_out_all_models_with_exclusive_filter_backend(self):
        """
        GET requests to ListCreateAPIView should return empty list when all models are filtered out.
        """
        root_view = RootView.as_view(filter_backends=(ExclusiveFilterBackend,))
        request = factory.get('/')
        response = root_view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_instance_view_filters_out_name_with_filter_backend(self):
        """
        GET requests to RetrieveUpdateDestroyAPIView should raise 404 when model filtered out.
        """
        instance_view = InstanceView.as_view(filter_backends=(ExclusiveFilterBackend,))
        request = factory.get('/1')
        response = instance_view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

    def test_get_instance_view_will_return_single_object_when_filter_does_not_exclude_it(self):
        """
        GET requests to RetrieveUpdateDestroyAPIView should return a single object when not excluded
        """
        instance_view = InstanceView.as_view(filter_backends=(InclusiveFilterBackend,))
        request = factory.get('/1')
        response = instance_view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'id': 1, 'text': 'foo'})

    def test_dynamic_serializer_form_in_browsable_api(self):
        """
        GET requests to ListCreateAPIView should return filtered list.
        """
        view = DynamicSerializerView.as_view()
        request = factory.get('/')
        response = view(request).render()
        self.assertContains(response, 'field_b')
        self.assertNotContains(response, 'field_a')


class TestGuardedQueryset(TestCase):
    def test_guarded_queryset(self):
        class QuerysetAccessError(generics.ListAPIView):
            queryset = BasicModel.objects.all()

            def get(self, request):
                return Response(list(self.queryset))

        view = QuerysetAccessError.as_view()
        request = factory.get('/')
        with pytest.raises(RuntimeError):
            view(request).render()
