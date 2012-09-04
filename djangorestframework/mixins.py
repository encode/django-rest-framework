from djangorestframework import status
from djangorestframework.response import Response


class MetadataMixin(object):
    """
    Should be mixed in with any `BaseView`.
    """
    def metadata(self, request, *args, **kwargs):
        content = {
            'name': self.get_name(),
            'description': self.get_description(),
            'renders': self._rendered_media_types,
            'parses': self._parsed_media_types,
        }
        #  TODO: Add 'fields', from serializer info.
        # form = self.get_bound_form()
        # if form is not None:
        #     field_name_types = {}
        #     for name, field in form.fields.iteritems():
        #         field_name_types[name] = field.__class__.__name__
        #     content['fields'] = field_name_types
        raise Response(content, status=status.HTTP_200_OK)


class CreateModelMixin(object):
    """
    Create a model instance.
    Should be mixed in with any `BaseView`.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA)
        if serializer.is_valid():
            self.object = serializer.object
            self.object.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.error_data, status=status.HTTP_400_BAD_REQUEST)


class ListModelMixin(object):
    """
    List a queryset.
    Should be mixed in with `MultipleObjectBaseView`.
    """
    def list(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        serializer = self.get_serializer(instance=self.object_list)
        return Response(serializer.data)


class RetrieveModelMixin(object):
    """
    Retrieve a model instance.
    Should be mixed in with `SingleObjectBaseView`.
    """
    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(instance=self.object)
        return Response(serializer.data)


class UpdateModelMixin(object):
    """
    Update a model instance.
    Should be mixed in with `SingleObjectBaseView`.
    """
    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.DATA, instance=self.object)
        if serializer.is_valid():
            self.object = serializer.object
            self.object.save()
            return Response(serializer.data)
        return Response(serializer.error_data, status=status.HTTP_400_BAD_REQUEST)


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    Should be mixed in with `SingleObjectBaseView`.
    """
    def destroy(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
