from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.http import HttpResponse

class AuthTokenLoginView(CreateAPIView):
    model = Token
    serializer_class = AuthTokenSerializer


class AuthTokenLogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated() and request.auth:
            request.auth.delete()
            return HttpResponse("logged out")
        else:
            return HttpResponse("not logged in")
    
