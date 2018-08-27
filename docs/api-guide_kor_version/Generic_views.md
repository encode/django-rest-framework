# Django REST Framework - Generic views

---

_"Django’s generic views... were developed as a shortcut for common usage patterns... They take certain common idioms and patterns found in view development and abstract them so that you can quickly write common views of data without having to repeat yourself."_  
_"Django의 generic views... 일반적인 사용 패턴을 위한 지름길로 개발되었습니다... 그들은 view 개발에서 발견되는 특정 공통 관용구와 패턴을 취해서 반복함으로써 반복하지 않고도 공통된 데이터 view를 빠르게 작성할 수 있습니다."_  
_— Django Documentation_

---

## Generic views
 CBV의 주요 이점 중 하나는 재사용이 가능한 동작을 구성하는 것입니다. REST 프레임워크는 일반적으로 사용되는 패턴을 제공하는 다수의 dict에 빌드 된 view를 제공함으로써 이를 활용합니다.  
REST 프레임워크에서 제공하는 generic view를 사용하면 데이터베이스 모델과 밀접하게 매핑되는 API 뷰를 빠르게 빌드 할 수 있습니다.  
`generic views` 가 API의 요구 사항에 맞지 않으면 정규 `APIView`클래스를 사용하여 drop down 하거나 `generic views`에서 사용하는 `mixin`과 기본 클래스를 재사용하여, 자신만 재사용이 가능한 `generic views` set를 작성할 수 있습니다.

### Examples
일반적으로 `generic views`를 사용하는 경우 view를 무시하고 여러 클래스 속성을 설정합니다.

```python
from django.contrib.auth.models import User
from myapp.serializers import UserSerializer
from rest_framework import generics
from rest_framework.permissions import IsAdminUser

class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
```
보다 복잡한 경우에는 view 클래스의 다양한 메서드를 재정의 할 수도 있습니다. 예를 들면:

```python
class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)
```
매우 간단한 경우에는 `.as_view()`메서드를 사용하여 클래스 속성을 전달할 수 있습니다. 예를 들어, `URLconf`에 다음 항목이 포함 될 수 있습니다.

```python
url(r'^/users/', ListCreateAPIView.as_view(queryset=User.objects.all(), serializer_class=UserSerializer), name='user-list')
```

---

## API Reference

### GenericAPIView
이 클래스는 REST 프레임워크의 `APIView` 클래스를 확장하여 기존 list view와 detail views에 일반적으로 필요한 동작을 추가합니다.  
제공된 각각의 `generic views`는 `GenericAPIView`를 하나 이상의 `minxin`클래스와 결합하여 빌드됩니다.

#### Attributes
##### Basic settings:
다음 속성은 기본 뷰 동작을 제어합니다.

- `queryset` : 이 뷰에서 객체를 반환하는 데 사용해야 하는 쿼리셋입니다. 일반적으로 이 속성을 설정하거나 `get_queryset()`메서드를 대체해야합니다. 뷰 메서드를 오버라이드하는 경우, 이 속성에 직접 액서스하는 대신 `get_queryset()`을 호출하는 것이 중요합니다. 쿼리셋은 한번 평가되고 그 결과는 모든 후속 request에 대해 캐시됩니다.
- `serializer_class` : 입력의 검증과 serializer 복원 및 출력 serializer에 사용하는 `serializer` 클래스입니다. 일반적으로 이 속성을 설정하거나 `get_serializer_class()`메소드를 대체해야 합니다.
- `lookup_field` : 개별 모델 인스턴스의 object 조회를 수행 할 때 사용해야하는 모델 필드입니다. 기본값은 `'pk'`입니다. 하이퍼링크 된 API에 custom 값을 사용해야 하는 경우 API views와 serializer 클래스가 `lookup`필드를 설정해야 합니다.
- `lookup_url_kwarg` : 객체 검색에 사용해야하는 URL 키워드 인수입니다. `URL conf`에는 이 값에 해당하는 키워드 인수가 포함되어야 합니다. 설정을 해제하면 `lookup_field`와 동일한 값을 사용합니다.

##### Pagination:
다음 속성은 list views와 함께 사용될 때 `pagination`을 제어하는데 사용됩니다.

- `pagination_class` : 결과 목록을 지정할 때 사용해야하는 `pagination`클래스입니다. 기본값은 `'rest_framework.pagination.PageNumberPagination'`인 `DEFAULT_PAGINATION_CLASS`설정과 동일한 값입니다. `pagination_class=None`으로 설정하면 이 view에서 pagination을 사용할 수 없습니다.  

##### Filtering:

- `filter_backends` : 쿼리셋을 필터링하는데 사용해야하는 `filter backend`클래스의 list입니다. 기본값은 `DEFAULT_FILTER_BACKENDS`설정과 동일합니다.

#### Method
##### Base methods:

```
get_queryset(self)
```
**`list view`**에서 사용되는 쿼리셋을 돌려줍니다. `detail view` 안의 `lookup`의 베이스로 사용됩니다. `queryset`속성에 의해 지정된 쿼리셋을 리턴하는 것이 기본값입니다.  
이 메서드는 `self.queryset`에 직접 액서스하는 대신 항상 사용되어야하며, `self.queryset`은 한번만 평가되고 그 결과는 모든 후속 요청에 캐시됩니다.  
request를 작성하는 사용자에게 특정되는 쿼리셋 반환과 같은 동적 동작을 제공하도록 재정의 될 수 있습니다.

예제:

```python
def get_queryset(self):
    user = self.request.user
    return user.accounts.all()
```

```
get_object(self)
```
**`detail views`**에 사용해야 하는 객체 인스턴스를 반환합니다. 기본적으로 `lookup_field` parameter를 사용하여 기본 쿼리셋을 필터링합니다.  
둘 이상의 `URL kwarg`를 기반으로 하는  `object lookups`와 같이 복잡한 동작을 제공하기 위해 무시될 수 있습니다.

예를 들어:

```python
def get_object(self):
    queryset = self.get_queryset()
    filter = {}
    for field in self.multiple_lookup_fields:
        filter[field] = self.kwargs[field]

    obj = get_object_or_404(queryset, **filter)
    self.check_object_permissions(self.request, obj)
    return obj
```
API에 객체 수준 권한이 없으면 선택적으로 `self.check_object_permissions`를 제외하고 단순히 `get_object_or_404` lookup에서 객체를 반환 할 수 있습니다.

```
filter_queryset(self, queryset)
```
**`serializer`**에 사용해야하는 클래스를 반환합니다. 기본값은 `serializer_class`속성을 반환하는 것입니다.  
읽기와 쓰기 작업에 다른 serializer를 사용하거나 다른 유형의 사용자에게 다른 serializer를 제공하는 등의 동적 동작을 제공하기 위해 재정의 될 수 있습니다.

예:

```python
def get_serializer_class(self):
    if self.request.user.is_staff:
        return FullAccountSerializer
    return BasicAccountSerializer
```

##### Save and deletion hooks:
다음과 같은 메서드가 `mixin`클래스에서 제공되며 object 저장이나 삭제 동작을 쉽게 대체 할 수 있습니다.

- `perform_create(self, serializer)` : 새 object 인스턴스를 저장할 때 `CreateModelMixin`에 의해 호출됩니다.
- `perform_update(self, serializer)` : 기존 object 인스턴스를 저장할 때 `UpdateModelMixin`에 의해 호출됩니다.
- `perform_destroy(self, instance)` : object 인스턴스를 삭제할 때 `DestroyModelMixin`에 의해 호출됩니다.

이러한 `hooks`는 request에 내포되어 있지만, 요청 데이터의 일부가 아닌 속성을 설정하는데 특히 유용합니다. 예를 들어, request 사용자를 기준으로 또는 URL 키워드 인수를 기반으로 object의 속성을 설정할 수 있습니다.

```python
def perform_create(self, serializer):
    serializer.save(user=self.request.user)
```
또한 이러한 오버라이드 포인트는 확인 이메일을 보내거나 업데이트를 로깅하는 것과 같이 object 저장 전후에 발생하는 동작을 추가 할 때 특히 유용합니다.
> 로깅 : 시스템을 작동할 때 시스템의 작동 상태의 기록,보존,시스템동작 분석들을 기록하는 것

```python
def perform_update(self, serializer):
    instance = serializer.save()
    send_email_confirmation(user=self.request.user, modified=instance)
```
`ValidationError()`를 발생시켜 추가 유효성 검사를 제공하기 위해 이러한 `hooks`을 사용할 수도 있습니다. 데이터베이스 저장 시점에 적용 할 유효성 검증 로직이 필요한 경우 유용 할 수 있습니다.

```python
def perform_create(self, serializer):
    queryset = SignupRequest.objects.filter(user=self.request.user)
    if queryset.exists():
        raise ValidationError('You have already signed up')
    serializer.save(user=self.request.user)
```

**Note**: 이 메서드는 이전 버전(2.x)의 `pre_save`, `post_save`, `pre_delete`와 `post_delete`메서드를 대체하며 더 이상 사용할 수 없습니다.  

##### Other methods:
`GenericAPIView`를 사용하여 custom views를 작성하는 경우, 호출할 수도 있지만 일반적으로 다음의 메서드를 대체하야 할 필요는 없습니다.

- `get_serializer_context(self)` : serializer에 제공되어야 하는 추가 컨텐스트가 포함된 dict를 반환합니다. 기본값엔 `request`, `view`, `format` 키가 포합됩니다.
- `get_serializer(self, instance=None, data=None, many=False, partial=False)` : serializer 인스턴스를 반환합니다.
- `get_paginated_response(self, data)` : pagination 스타일의 response object를 반환합니다.
- `paginate_queryset(self, queryset)` : 필요하면, `paginate_queryset`에 page object를 반환하거나, 이 view에 pagination이 구성되지 않은 경우 None을 반환합니다.
- `filter_queryset(self, queryset)` : 주어진 쿼리셋을 사용중인 필터 백엔드를 사용하여 새로운 쿼리셋을 반환합니다.

---

## Mixins
`mixin`클래스는 기본 view 동작을 제공하는데 사용되는 작업을 제공합니다. `mixin`클래스는 `.get()`와 `.post()`와 같은 핸들러 메서드를 직접 정의하는 것이 아니라 작업 메서드를 제공합니다. 이것은 보다 유연한 작동 구성을 가능하게 합니다.  
`mixin`클래스는 `rest_framework.mixins`에서 가져 올 수 있습니다.

### ListModelMixin
쿼리셋 list를 구현하는 `.list(request, *args, **kwargs)`메서드를 제공합니다.  
쿼리셋이 채워지면 response의 본문으로 쿼리셋의 serializer 된 표현과 함께 `200 OK`응답을 반환합니다. response 데이터는 선택적으로 페이징 될 수 있습니다.

### CreateModelMixin
새 모델 인스턴스 만들기 및 저장을 구현하는 `.create(request, *args, **kwargs)`메서드를 제공합니다.  
객체가 생성되면 객체의 serializer 된 표현을 response의 본문으로 사용하여 `201 Created`응답을 반환합니다. 표현에 `url`이라는 키가 포함되어 있으면 response의 `Location` 헤더가 해당 값으로 채워집니다.  
객체 생성을 위해 제공된 request 데이터가 유효하지 않은 경우 `400 Bad Request`응답이 반환되며, 오류 내역은 response 본문으로 반환됩니다.

### RetrieveModelMixin
response에서 기존 모델 인스턴스를 반환하도록 구현하는 `.retrieve(request, *args, **kwargs)`메서드를 반환합니다.  
객체를 검색 할 수 있는 경우 `200 OK`응답을 반환하며, 객체를 response 본문으로 serializer하여 반환합니다.

### UpdateModelMixin
기존 모델 인스턴스를 업데이트하고 저장하는 `.update(request, *args, **kwargs)`메서드를 제공합니다.  
또한 `update`메소드와 유사한 `.partial_update(request, *args, **kwargs)`메소드도 제공합니다. 단, 업데이트의 모든 필드는 선택사항입니다. 이렇게 하면 HTTP`PATCH`request를 지원할 수 있습니다.  
객체가 업데이트되면 객체의 serializer 된 표현이 응답 본문과 함께 `200 OK`응답을 반환합니다.  
객체를 업데이트하기 위해 제공된 request 데이터가 유효하지 않은 경우 `400  Bad Request`응답이 반환되고 오류 세부 정보가 response 본문으로 사용됩니다.

### DestroyModelMixin
기존 모델 인스턴스의 삭제를 구현하는 `.destroy(request, *args, **kwargs)`메서드를 제공합니다.  
객체가 삭제되면 `204 No Content`응답을 반환하고, 그렇지 않으면 `404 Not Found`을 반환합니다.

--- 

## Concrete View Classes
다음의 클래스는 구체적인 `generic views`입니다. `generic views`를 사용하는 경우 일반적을 커스터마이징 된 동작이 필요하지 않으면 할만한 수준입니다.  
뷰 클래스는 `rest_framework.generics`에서 가져올 수 있습니다.

### CreateAPIView
**읽기 전용** 엔드포인트에 사용됩니다.  
`post` 메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [CreateModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#createmodelmixin)

### ListAPIView
**읽기 전용** 엔드포인트가 **모델 인스턴스의 콜렉션**을 나타내는데 사용됩니다.  
`get` 메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [ListModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#listmodelmixin)

### RetrieveAPIView
**읽기 전용** 엔드포인트가 **단일 모델 인스턴스**를 나타내는데  사용됩니다.  
`get`메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [RetrieveModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#retrievemodelmixin)

### DestroyAPIView
**삭제 전용** 엔드포인트가 **단일 모델 인스턴스**를 나타내는데 사용됩니다.  
`delete`메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [DestroyModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#destroymodelmixin)

### UpdateAPIView
**업데이트 전용** 엔드포인트가 **단일 모델 인스턴스**를 나타내는데 사용됩니다.  
`put`과 `patch`메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [UpdateModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#updatemodelmixin)

### ListCreateAPIView
**읽기-쓰기** 엔드포인트가 **모델 인스턴스의 컬렉션**를 나타내는데 사용됩니다.  
`get`과 `post` 메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [ListModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#listmodelmixin), [CreateModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#createmodelmixin)

### RetrieveUpdateAPIView
**읽거나 업데이트** 엔드포인트가 **단일 모델 인스턴스**를 나타내는데 사용됩니다.  
`get`, `put`, `patch` 메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [RetrieveModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#retrievemodelmixin), [UpdateModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#updatemodelmixin)

### RetrieveDestroyAPIView
**읽거나 삭제** 엔드포인트가 **단일 모델 인스턴스**를 나타내는데 사용됩니다.  
`get`과 `delete`메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [RetrieveModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#retrievemodelmixin), [DestroyModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#destroymodelmixin)

### RetrieveUpdateDestroyAPIView
**읽기-쓰기-삭제** 엔드포인트가 **단일 모델 인스턴스**를 나타내는데 사용됩니다.  
`get`, `put`, `patch`, `delete`메서드 핸들러를 제공합니다.  
Extends: [GenericAPIView](http://www.django-rest-framework.org/api-guide/generic-views/#genericapiview), [RetrieveModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#retrievemodelmixin), [UpdateModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#updatemodelmixin), [DestroyModelMixin](http://www.django-rest-framework.org/api-guide/generic-views/#destroymodelmixin)

---

## Customizing the generic views
종종 기본 generic views를 사용하고 약간 custom 된 동작을 사용하려고 합니다. 여러 위치에서 custom 된 동작을 재사용하는 경우, 동작을 공통 클래스로 리팩토링하여 필요할 때 모든 view나 viewset에 적용할 수 있습니다.

### Creating custom mixins
예를 들어, URL conf 내의 복수의 필드에 근거해 오브젝트를 검색 할 필요가 있는 경우, 다음과 같이 `mixin` 클래스를 작성할 수 있습니다.

```python
class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()             # 기본 쿼리셋 가져오기
        queryset = self.filter_queryset(queryset)  # backends에서 필터 적용
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]: # 빈 필드는 무시
                filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)  # 객체를 찾는다
```
그런 다음 custom 동작을 적용해야 할때 mixin을 view나 viewset에 간단하게 적용할 수 있습니다.

```python
class RetrieveUserView(MultipleFieldLookupMixin, generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_fields = ('account', 'username')
```
사용해야 하는 custom 동작이 있는 경우, custom mixin을 사용하는 것이 좋습니다.

### Creating custom base classes
여러 views에서 mixin을 사용하는 경우, 이 단계를 더 진행하고 프로젝트 전체에서 사용할 수 있는 고유한 기본 views set을 만들 수 있습니다. 예를 들어:

```python
class BaseRetrieveView(MultipleFieldLookupMixin,
                       generics.RetrieveAPIView):
    pass

class BaseRetrieveUpdateDestroyView(MultipleFieldLookupMixin,
                                    generics.RetrieveUpdateDestroyAPIView):
    pass
```
프로젝트 전반에 걸쳐 많은 수의 views에서 일관되게 반복해야 하는 custom 동작이 있는 경우, custom 기본 클래스를 사용하는 것이 좋습니다.

---

## PUT as create
버전 3.0 이전에는 객체가 이미 존재하는지 여부에 따라 REST 프레임워크 mixins가 `PUT`을 업데이트나 작성 작업으로 처리했습니다.  
생성 작업으로 `PUT`을 허용하는 것은 객체의 존재나 부재에 대한 정보를 반드시 노출시키기 때문에 문제가 됩니다. 또한 이전에 삭제 된 인스턴스를 투명하게 다시 만들수 있다는 것이 단순히 `404`응답을 반환하는 것보다 더 나은 기본 동작이라고 할 수만은 없습니다.  
"`PUT` as 404"와 "`PUT` as create"는 서로 다른 상황에서 유효 할 수 있지만, 버전 3.0부터는 더 간단하고 명확한 404 동작을 기본값으로 사용합니다.  
일반적인 `PUT-as-create`동작이 필요한 경우 `AllowPUTAsCreateMixin`클래스를 views에 mixin으로 포함할 수 있습니다.

---

## Third party packages
다음의 타사 패키지는 추가 generic view 구현을 제공합니다.

### Django REST Framework bulk
[django-rest-framework-bulk](https://github.com/miki725/django-rest-framework-bulk)패키지는 API request을 통해 대량 작업을 적용할 수 있도록 generic views mixin 뿐만 아니라 일반적인 구체적 generic views를 구현합니다.

### Django Rest Multiple Models
[Django Rest Multiple Models](https://github.com/Axiologue/DjangoRestMultipleModels)은 단일 API request을 통해 여러 serializer된 모델 및 `/` 또는 쿼리셋을 전송하기 위한 generic views(and mixin)을 제공합니다.
