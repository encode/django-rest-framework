from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from . import models, serializers


class SummaryViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = models.Summary.objects.all()
    serializer_class = serializers.SummarySerializer
    permission_classes = [AllowAny]
