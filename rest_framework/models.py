from django.core.exceptions import NON_FIELD_ERRORS
from django.db import models
from .views import APIView
from .response import Response
from . import serializers, status


class EasyAPI(models.Model, APIView):
    """
    Inherite EasyAPI class and create models as you were creating.
    You need to add a url with the class.
    For example:

    in models.py

    class MyClass(EasyAPI):
        field1 = models.CharField(max_length=100)

    in urls.py
    from .models import MyClass

    urlpaterns = [
        path('myurl/', MyClass.as_view())
    ]
    """
    def get(self, request, *args, **kwargs):
        

        class EasyAPISerializer(serializers.ModelSerializer):
            class Meta:
                fields = '__all__'
                model = self.__class__

        self.child_model = self.__class__
        
        pk = None
        if 'id' in request.query_params:
            pk = request.query_params['id']

        try:
            queryset = self.__class__.objects.all() if pk is None else self.__class__.objects.get(pk=pk)
        except self.__class__.DoesNotExist:
            return Response({'msg': f'object with id={pk} does not exists'}, status=status.HTTP_404_NOT_FOUND)
        if pk is None:
            easyapi_serializer = EasyAPISerializer(queryset, many=True)
        else:
            easyapi_serializer = EasyAPISerializer(queryset)

        return Response(easyapi_serializer.data)
    
    def post(self, request, *args, **kwargs):
        
        class EasyAPISerializer(serializers.ModelSerializer):
            class Meta:
                fields = '__all__'
                model = self.__class__

        easyapi_serializer = EasyAPISerializer(data=request.data)
        easyapi_serializer.is_valid(raise_exception=True)
        easyapi_serializer.save()

        return Response(easyapi_serializer.data)
    
    def put(self, request, *args, **kwargs):
        
        pk = None
        if 'id' not in request.query_params:
            return Response({'msg': 'id parameter not present.'}, status=status.HTTP_400_BAD_REQUEST)

        pk = request.query_params['id']

        class EasyAPISerializer(serializers.ModelSerializer):
            class Meta:
                fields = '__all__'
                model = self.__class__
        try:
            queryset =self.__class__.objects.get(pk=pk)
            easy_serializer = EasyAPISerializer(queryset, data=request.data, partial=True)
            easy_serializer.is_valid(raise_exception=True)
            easy_serializer.save()

            return Response(easy_serializer.data)
        except self.__class__.DoesNotExist:
            return Response({'msg': f'object with id={pk} does not exists'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        
        pk = None
        if 'id' not in request.query_params:
            return Response({'msg': 'id parameter not present.'}, status=status.HTTP_400_BAD_REQUEST)
        
        pk = request.query_params['id']

        queryset =self.__class__.objects.filter(pk=pk)

        if len(queryset)==0:
            return Response({'msg': f'object with id={pk} does not exists'}, status=status.HTTP_404_NOT_FOUND)

        queryset.delete()
        return Response({'msg': 'Object deleted'})
    
    class Meta:
        abstract = True
