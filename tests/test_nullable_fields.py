# from django.core.urlresolvers import reverse

# from django.conf.urls import patterns, url
# from rest_framework import serializers, generics
# from rest_framework.test import APITestCase
# from tests.models import NullableForeignKeySource


# class NullableFKSourceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NullableForeignKeySource


# class NullableFKSourceDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = NullableForeignKeySource.objects.all()
#     serializer_class = NullableFKSourceSerializer


# urlpatterns = patterns(
#     '',
#     url(r'^objects/(?P<pk>\d+)/$', NullableFKSourceDetail.as_view(), name='object-detail'),
# )


# class NullableForeignKeyTests(APITestCase):
#     """
#     DRF should be able to handle nullable foreign keys when a test
#     Client POST/PUT request is made with its own serialized object.
#     """
#     urls = 'tests.test_nullable_fields'

#     def test_updating_object_with_null_fk(self):
#         obj = NullableForeignKeySource(name='example', target=None)
#         obj.save()
#         serialized_data = NullableFKSourceSerializer(obj).data

#         response = self.client.put(reverse('object-detail', args=[obj.pk]), serialized_data)

#         self.assertEqual(response.data, serialized_data)
