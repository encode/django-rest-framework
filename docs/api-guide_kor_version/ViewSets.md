# Django REST Framework - ViewSets

---

_"After routing has determined which controller to use for a request, your controller is responsible for making sense of the request and producing the appropriate output."_  

_"라우팅에서 request에 사용할 컨트롤러를 결정한 후에 컨트롤러는 request를 이해하고 적절한 출력을 생성해야합니다."_  

_— Ruby on Rails Documentation_  

---

## ViewSets	
Django REST 프레임워크를 사용하면 `ViewSet`이라고하는 단일 클래스에서 `ViewSet`에 대한 논리를 결합할 수 있습니다. 다른 프레임워크에서는 `Resources`나 `Controllers`와 같은 개념적으로 유사한 구현을 찾을 수도 있습니다.  
`ViewSet` 클래스는 단순히 `.get()`이나 `.post()`과 같은 메소드 핸들러를 제공하지 않고 CBV 유형이며, 대신 `.list()`와 `.create()`와 같은 액션을 제공합니다.  
`ViewSet`의 메서드 핸들러는 `.as_view()`메서드를 사용하여 뷰를 마무리하는 시점의 해당 액션에만 바인딩됩니다.
>바인딩 : 각종 값들이 확정되어 더이상 변경 할 수 없는 상태가 되는것. 식별자(identifier)가 그 대상인 메모리 주소, 데이터형 또는 실제값으로 배정되는 것

일반적으로 urlconf의 viewset에 뷰를 명시적을 등록하는 대신 viewset을 `router`클래스로 등록하면 자동으로 urlconf가 결정됩니다.

### Example
시스템의 모든 사용자를 나열하거나 검색하는데 사용 할 수 있는 간단한 viewset을 정의합시다.

```python
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from myapps.serializers import UserSerializer
from rest_framework import viewsets
from rest_framework.response import Response

class UserViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    def list(self, request):
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)
```
필요한 경우 이 viewset을 다음과 같이 두 개의 개별 뷰 바인딩 할 수 있습니다.

```python
user_list = UserViewSet.as_view({'get': 'list'})
user_detail = UserViewSet.as_view({'get': 'retrieve'})
```
평소엔 우리는 이것을 하지 않을 것이지만, 대신 viewset을 라우터에 등록하고 urlconf가 자동으로 생성되도록 할 것입니다. 

```python
from myapp.views import UserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet)
urlpatterns = router.urls
```
자신만의 viewset를 작성하는 대신, 기본 동작 set을 제공하는 기존 기본 클래스를 사용하는 것이 좋습니다. 예를 들어:

```python
class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
```
`View` 클래스를 사용하는 것보다 `ViewSet`클래스를 사용하는 두 가지 주요 이점이 있습니다.

- 반복 논리를 하나의 클래스로 결합 할 수 있습니다. 위의 예에서 쿼리셋은 한번만 지정하면 여러 view에서 사용됩니다.
- router를 사용함으로써 우리는 더 이상 URLconf의 연결을 처리 할 필요가 없습니다.  

이 두가지 모두 장단점이 있습니다. 일반 views와 URL conf를 사용하면 보다 명확하게 제어할 수 있습니다. `ViewSet`는 신속하게 시작하고 실행하려는 경우, 또는 대규모 API가 있고 전체적으로 일관된 URL conf를 적용하려는 경우 유용합니다.

### Marking extra actions for routing
REST 프레임워크에 포함 된 기본 router는 아래와 같이 `creste`/`retirieve`/`update`/`destroy` 스타일 작업의 기본 set을 위한 경로를 제공합니다.

```python
class UserViewSet(viewsets.ViewSet):
    """
    Example empty viewset demonstrating the standard
    actions that will be handled by a router class.

    If you're using format suffixes, make sure to also include
    the `format=None` keyword argument for each action.
    """

    def list(self, request):
        pass

    def create(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
```
라우팅해야 하는 임시 메소드가 있는 경우 `@detail_router`나 `@list_router`데코레이터를 사용하여 라우팅을 요구하는 것으로 표시 할 수 있습니다.  
`@detail_router`데코레이터는 URL 패턴에 `pk`를 포함하며 단일 인스턴스가 필요한 메소드용입니다. `@list_router`데코레이터는 객체 목록에서 작동하는 메소드를 대상으로 합니다.

예를 들어:

```python
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from myapp.serializers import UserSerializer, PasswordSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @detail_route(methods=['post'])
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.data['password'])
            user.save()
            return Response({'status': 'password set'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route()
    def recent_users(self, request):
        recent_users = User.objects.all().order('-last_login')

        page = self.paginate_queryset(recent_users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(recent_users, many=True)
        return Response(serializer.data)
```
데코레이터는 라우트 된 뷰에 대해서만 설정 할 추가 인수를 추가로 취할 수 있습니다. 예를 들어..

```python
    @detail_route(methods=['post'], permission_classes=[IsAdminOrIsSelf])
    def set_password(self, request, pk=None):
       ...
```
이러한 데코레이터는 기본적으로 `GET` request를 라우트하지만 `methods`인수를 사용하여 다른 HTTP 메소드를 채택할 수도 있습니다. 예:

```python
    @detail_route(methods=['post', 'delete'])
    def unset_password(self, request, pk=None):
       ...
```
두 개의 작업은  `^users/{pk}/set_password/$` 과 `^users/{pk}/unset_password/$`에서 사용 할 수 있습니다.

---

## API Reference

### ViewSet
`ViewSet`클래스는 `APIView`에서 상속받습니다. viewset에 대한 API 정책을 제어하기 위해 `permission_classes`,`authentication_classes`와 같은 표준 속성을 사용할 수 있습니다.  
`ViewSet` 클래스는 액션의 구현을 제공하지 않습니다. `ViewSet` 클래스를 사용하려면 클래스를 오버라이트하고 액션 구현을 명시적으로 정의해야합니다.

### GenericViewSet
`GenericViewSet`클래스는 `GenericAPIView`에서 상속되며, `get_object`, `get_queryset`메소드와 그 외 `generic view`의  기본 동작의 기본 set을 제공하지만, 기본적으로 어떤 액션도 포함하지 않습니다.  
`GenericViewSet`클래스를 사용하려면 클래스를 재정의하고 필요한 `mixin`클래스를 혼합하거나 액션 구현을 명시적으로 정의하세요.

### ModelViewSet
`ModelViewSet`클래스는 `GenericAPIView`를 상속하며, 다양한 `mixin`클래스의 동작을 혼합하여 다양한 액션에 대한 구현을 포함합니다.  
`ModelViewSet`클래스에서 제공하는 작업은 `.list()`, `.retrieve()`, `.create()`, `.update()`, `.partial_update()`, `.destroy()`입니다.

#### Example
`ModelViewSet`은 `GenericAPIView`를 확장하기 때문에 일반적으로 적어도 `queryset`과 `serializer_class` 속성을 제공해야 합니다. 예:

```python
class AccountViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAccountAdminOrReadOnly]
```
`GenericAPIView`가 제공하는 표준 속성이나 메소드 오버라이드를 사용할 수 있습니다. 예를 들어, 작동해야하는 쿼리셋을 동적으로 결정하는 viewset을 사용하려면 다음과 같이 할 수 있습니다.

```python
class AccountViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing the accounts
    associated with the user.
    """
    serializer_class = AccountSerializer
    permission_classes = [IsAccountAdminOrReadOnly]

    def get_queryset(self):
        return self.request.user.accounts.all()
```
그러나 `ViewSet`에서 `queryset` 속성을 제거하면 연관된 [라우터](http://www.django-rest-framework.org/api-guide/routers/)가 모델의 `base_name`을 자동으로 파생시킬 수 없으므로 [라우터 등록](http://www.django-rest-framework.org/api-guide/routers/)의 일부로 `base_name kwarg`를 지정해야합니다.  
또한 이 클래스는 기본적으로 `create`/`list`/`retrieve`/`update`/`destroy` 액션의 전체 set을 제공하지만 표준 권한 클래스를 사용하여 사용 가능한 작업을 제한할 수 있습니다.

### ReadOnlyModelViewSet
`ReadOnlyModelViewSet`클래스 또한 `GenericAPIView`에서 상속받습니다. `ModelViewSet`과 마찬가지로 다양한 액션에 대한 구현도 포함되지만 `ModelViewSet`과 달리 **일기 전용**동작인 `.list()`, `.retrieve()`만 제공됩니다.

#### Example
`ModelViewSet`에서와 같이 일반적으로 적어도 `queryset`과 `serializer_class`속성을 제공해야 합니다. 예:

```python
class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing accounts.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
```
`ModelViewSet`과 마찬가지로 `GenericAPIView`에서 사용할 수 있는 표준 속성과 메소드 오버라이드를 사용할 수 있습니다.

## Custom ViewSet base classes
`ModelViewSet` 액션의 전체 set이 없거나 다른 방식으로 동작을 사용자 정의하는 custom `ViewSet`클래스를 제공해야 할 수도 있습니다.

### Example
`create`, `list`, `retrieve` 조작을 제공하고, `GenericViewSet`에서 상속하며, 필요한 조치를 `mixin`하는 기본 viewset를 작성하려면 다음을 작성하세요.

```python
class CreateListRetrieveViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    `retrieve`, `create`, `list` actions을 제공하는 viewset입니다.

    이것들을 사용하려면 클래스와  `.queryset`과 
    `.serializer_class`의 속성을 오버라이드하세요.
    """
    pass
```
고유한 기본 `ViewSet`클래스를 작성하여 API 전반에 걸쳐 여러 viewset에서 재사용 할 수 있는 공통적인 동작을 제공할 수 있습니다.
