# Django REST Framework - Permissions

---
_"Authentication or identification by itself is not usually sufficient to gain access to information or code. For that, the entity requesting access must have authorization."_  

_"정보 또는 코드에 대한 액서스 권한을 얻으려면 일반적으로 인증이나 식별만으로는 충분하지 않습니다. 이를 위해서는 액서스를 요청하는 개체에 권한이 있어야합니다."_  

_— Apple Developer Documentation_

---

## Permissions
[인증](http://www.django-rest-framework.org/api-guide/authentication/) 및 [제한](http://www.django-rest-framework.org/api-guide/throttling/)과 함께 사용 권한은 request에 액서스를 허용할지 또는 거부 할지를 결정합니다.  
권한 검사는 다른 코드가 진행되기 전에 view의 맨 처음에 항상 실행됩니다. 권한 검사는 일반적으로 들어오는 request를 허용해야 하는지를 결정하기 위해 `request.user`및 `request.auth` 등록 정보의 인증 정보를 사용합니다.  
권한은 다른 클래스의 사용자가 API의 다른 부분에 액서스 하는 것을 허용하거나 거부하는게 사용됩니다.  
가장 간단한 사용 권한 스타일은 인증 된 사용자에게 멕서스를 허용하고 인증되지 않은 모든 사용자에 대한 엑서스를 거부하는 것입니다. 이것은 REST프레임워크의 `IsAuthenticated`클래스에 해당합니다.  
약간 덜 엄격한 권한 스타일은 인증 된 사용자에게 모든 권한을 허용하지만 인증되지 않은 사용자에게는 읽기전용 권한을 허용하는 것입니다. 이것은 REST 프레임워크의 `IsAuthenticatedOrReadOnly` 클래스에 해당합니다.

### How permissions are determined
REST 프레임워크의 권한은 항상 클래스 list로 정의됩니다.  
뷰의 본문을 실행하기 전에 list의 각 권한이 검사됩니다. 권한 확인에 실패하면 `exceptions.PermissionDenied` 또는 `exceptions.NotAuthenticated` 예외가 발생하고 view 본문이 실행되지 않습니다.  
권한 검사가 실패하면 다음 규칙에 따라 "403 Forbidden"또는 "401 Unauthorized"응답이 반환됩니다.

- 요청이 성공적으로 인증되었지만 권한이 거부되었습니다. - HTTP 403 Forbidden 응답이 리턴됩니다.
- 요청이 성공적으로 인증되지 않았고 최상위 우선 순위 인증 클래스는 `WWW-Authenticate` 헤더를 사용하지 않습니다. - HTTP 403 Forbidden 응답이 리턴됩니다.
- 요청이 성공적으로 인증되지 않았고 최상위 우선 순위 인증 클래스는 `WWW-Authenticate` 헤더를 사용합니다. - 적절한 `WWW-Authenticate` 헤더가 있는 HTTP 401 Unauthorized 응답이 반환됩니다.

### Object level permissions
REST 프레임워크 권한은 또한 오브젝트 레벨 권한 부여를 지원합니다. 개체 수준 권한은 사용자가 특정 개체(일반적으로 모델 인스턴스)에 대한 작업을 허용해야하는지 여부를 결정하는 데 사용됩니다.  
객체 레벨 권한은 `.get_object()`가 호출 될 때 REST 프레임워크의 generic view에 의해 실행됩니다. 뷰 수준 권한과 마찬가지로, 사용자가 지정된 객체를 처리할 수 없는 경우 `exceptions.PermissionDenied` 예외가 발생합니다.  
자신 만의 뷰를 작성하고 오브젝트 레벨 권한을 적용하려는 경우 또는 generic 뷰에서 `get_object` 메소드를 겹쳐 쓰는 경우에는, 개체를 검색 한 시점에서 뷰에서 `.check_object_permissions(request, obj)` 메소드를 명시적으로 호출해야합니다.  
`PermissionDenied` 또는 `NotAuthenticated` 예외가 발생하거나 view에 적절한 권한이 있는 경우 반환됩니다.
예:

```python
def get_object(self):
    obj = get_object_or_404(self.get_queryset())
    self.check_object_permissions(self.request, obj)
    return obj
```
#### Limitations of object level permissions(개체 수준 사용 권한의 제한 사항)
성능 상의 이유로 generic view는 오브젝트 목록을 리턴 할 때 queryset의 각 인스턴스에 오브젝트 레벨 권한을 자동으로 적용하지 않습니다.  
객체 레벨 권한을 사용하는 경우 종종 [쿼리 세트를 적절히 필터링](http://www.django-rest-framework.org/api-guide/filtering/)하여 사용자가 볼 수있는 인스턴스에 대한 가시성만 확보하도록 하는 것이 좋습니다.

### Setting the permission policy
기본 권한 정책은 `DEFAULT_PERMISSION_CLASSES` 설정을 사용하여 전역으로 설정할 수 있습니다. 예를 들면.

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}
```
지정하지 않으면이 설정은 기본적으로 무제한 액세스를 허용합니다.

```python
'DEFAULT_PERMISSION_CLASSES': (
   'rest_framework.permissions.AllowAny',
)
```
또한 `APIView` CBV를 사용하여 view 별 또는 view 별 기준별로 인증 정책을 설정할 수 있습니다.

```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class ExampleView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)
```
또는 FBV와 함께 @api_view` 데코레이터를 사용하는 경우.

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def example_view(request, format=None):
    content = {
        'status': 'request was permitted'
    }
    return Response(content)
```
**Note**: 클래스 속성이나 데코레이터를 통해 새 권한 클래스를 설정하면 **settings.py** 파일을 통해 설정된 기본 목록을 무시하도록 뷰에 지시합니다.

---

## API Reference
### AllowAny
`AllowAny` 권한 클래스는 **요청이 인증되었거나 인증되지 않았는지 여부에 관계없이** 제한되지 않은 액세스를 허용합니다.  
사용 권한 설정에 빈 목록이나 튜플을 사용하여 동일한 결과를 얻을 수 있기 때문에 이 사용 권한은 반드시 필요한 것은 아니지만 의도를 명시적으로 지정하기 때문에 이 클래스를 지정하는 것이 유용 할 수 있습니다.

### IsAuthenticated
`IsAuthenticated` 권한 클래스는 인증되지 않은 사용자에게 권한을 거부하고 그렇지 않은 경우에는 권한을 허용합니다.  
 이 권한은 등록 된 사용자만 API에 액세스 할 수 있게 하려는 경우 적합합니다.  
 
### IsAdminUser
`IsAdminUser` 권한 클래스는 `user.is_staff`가 `True` 인 경우를 제외하고 모든 사용자에 대한 사용 권한을 거부합니다.  

이 권한은 신뢰할 수 있는 관리자의 하위 집합에서만 API에 액세스 할 수 있게 하려는 경우 적합합니다.

### IsAuthenticatedOrReadOnly
`IsAuthenticatedOrReadOnly`를 사용하면 인증 된 사용자가 모든 요청을 수행 할 수 있습니다. 
권한이 없는 사용자에 대한 요청은 요청 방법이 **"안전한"**방법 중 하나일 경우에만 허용됩니다. `GET`, `HEAD` 또는 `OPTIONS`.  
이 권한은 API에서 익명 사용자에게 읽기 권한을 허용하고 인증 된 사용자에게만 쓰기 권한을 허용하려는 경우에 적합합니다.  

### DjangoModelPermissions
이 퍼미션 클래스는 Django의 표준 `django.contrib.auth` [모델 퍼미션](https://docs.djangoproject.com/en/1.10/topics/auth/customizing/#custom-permissions)과 관련이 있습니다. 이 권한은 `.queryset` 속성이 설정된 view에만 적용해야합니다. 권한 부여는 사용자가 인증되고 관련 모델 권한이 할당 된 경우에만 부여됩니다.  

- `POST` request를 사용하려면 사용자에게 모델에 대한 `add` 권한이 있어야합니다.
- `PUT` 및 `PATCH` request는 사용자가 모델에 대한 변경 권한을 요구합니다.
- `DELETE` request는 사용자에게 모델에 대한 삭제 권한이 있어야합니다.

기본 동작을 재정의하여 사용자 지정 모델 권한을 지원할 수도 있습니다. 예를 들어 `GET` 요청에 대한 view 모델 권한을 포함 할 수 있습니다.  
custom 모델 권한을 `DjangoModelPermissions`을 오버라이드하고 `.perms_map` property를 설정하여 사용합니다.

#### Using with views that do not include a queryset attribute. (queryset 속성을 포함하지 않는 뷰를 사용할 때)
재정의 된 `get_queryset()` 메서드를 사용하는 뷰에서 이 권한을 사용하는 경우 뷰에 `queryset` 속성이 없을 수 있습니다. 이 경우에는 sentinel queryset으로 뷰를 표시하여 이 클래스가 필요한 권한을 결정할 수 있도록하는 것이 좋습니다. 예 :

```
queryset = User.objects.none()  # Required for DjangoModelPermissions
```

### DjangoModelPermissionsOrAnonReadOnly
`DjangoModelPermissions`와 유사하지만 인증되지 않은 사용자는 API에 대한 읽기 전용 액세스만 허용합니다.

### DjangoObjectPermissions
이 퍼미션 클래스는 모델에 대한 객체 별 권한을 허용하는 Django의 표준 [객체 권한 프레임워크](https://docs.djangoproject.com/en/1.10/topics/auth/customizing/#handling-object-permissions)와 관련이있다. 이 권한 클래스를 사용하려면 [`django-guardian`](https://github.com/django-guardian/django-guardian)과 같은 객체 수준 권한을 지원하는 권한 백엔드를 추가해야합니다.  
`DjangoModelPermissions`와 마찬가지로 이 권한은 `.queryset` 속성이나 `.get_queryset()` 메소드가 있는 뷰에만 적용되어야합니다. 권한 부여는 사용자가 인증되고 관련 객체 별 권한 및 관련 모델 권한이 할당 된 경우에만 부여됩니다.

- `POST` request는 사용자에게 모델 인스턴스에 대한 추가 권한이 필요합니다.
- `PUT` 및 `PATCH` request는 사용자가 모델 인스턴스에 대한 변경 권한을 요구합니다.
- `DELETE` 요청은 사용자에게 모델 인스턴스에 대한 삭제 권한이 있어야합니다.

`DjangoObjectPermissions`는 `django-guardian` 패키지를 **필요로 하지 않으며** 다른 객체 레벨 백엔드도 똑같이 잘 지원해야합니다.  
`DjangoModelPermissions`와 마찬가지로 `DjangoObjectPermissions`를 재정의하고 `.perms_map` 속성을 설정하여 사용자 정의 모델 권한을 사용할 수 있습니다. 자세한 내용은 소스 코드를 참조하십시오.

---
**Note**: `GET`, `HEAD` 및 `OPTIONS` request에 대한 객체 수준 view 권한이 필요하면 `DjangoObjectPermissionsFilter` 클래스를 추가하여 목록 엔드포인트가 사용자에게 적절한 뷰 권한이 있는 객체를 포함하여 결과만 반환하도록 해야합니다.

---

## Custom permissions
Custom 권한을 구현하려면, `BasePermission`를 무시하고 다음 중 하나 또는 두가지 방법을 구현합니다.

- `.has_permission(self, request, view)`
- `.has_object_permission(self, request, view, obj) `

request에 액세스 권한이 부여되면 메서드는 `True`를 반환하고 그렇지 않으면 `False`를 반환해야합니다.  
request가 읽기 작업인지 쓰기 작업인지 테스트해야하는 경우 `'GET'`, `'OPTIONS'`및 `'HEAD'`가 포함 된 튜플 인 `SAFE_METHODS` 상수와 비교하여 request 메소드를 확인해야합니다. 예:

```python
if request.method in permissions.SAFE_METHODS:
    # 읽기 전용 액세스 권한을 확인하려면
else:
    # 쓰기 액세스 권한을 확인하려면
```

---
**Note**: 뷰 수준 `has_permission` 검사가 이미 통과 된 경우에만 인스턴스 수준의 `has_object_permission` 메소드가 호출됩니다. 또한 인스턴스 수준 검사를 실행하려면 view 코드에서 `.check_object_permissions(request, obj)`를 명시적으로 호출해야 합니다. generic view를 사용하는 경우 기본적으로 이 옵션이 처리됩니다.

---

테스트가 실패 할 경우 custom 권한은 `PermissionDenied` 예외를 발생시킵니다. 예외와 관련된 오류 메시지를 변경하려면 custom 권한에 직접 `massege` 속성을 구현하십시오. 그렇지 않으면 `PermissionDenied`의 `default_detail` 속성이 사용됩니다.

```python
from rest_framework import permissions

class CustomerAccessPermission(permissions.BasePermission):
    message = 'Adding customers not allowed.'

    def has_permission(self, request, view):
         ...
```

### Examples
다음은 들어오는 request의 IP 주소를 블랙리스트와 대조하여 IP가 블랙리스트에 올랐으면 request를 거부하는 권한 클래스의 예입니다.

```python
from rest_framework import permissions

class BlacklistPermission(permissions.BasePermission):
    """
    Global permission check for blacklisted IPs.
    """

    def has_permission(self, request, view):
        ip_addr = request.META['REMOTE_ADDR']
        blacklisted = Blacklist.objects.filter(ip_addr=ip_addr).exists()
        return not blacklisted
```
들어오는 모든 request에 ​​대해 실행되는 전역 권한뿐 아니라 특정 개체 인스턴스에 영향을 주는 작업에 대해서만 실행되는 개체 수준 사용 권한을 만들 수도 있습니다. 예 :

```python
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # 읽기 권한은 모든 요청에 ​​허용되며,
        # 그래서 GET, HEAD, OPTIONS 요청을 허용 할 것입니다.
        if request.method in permissions.SAFE_METHODS:
            return True

        # 인스턴스에는`owner`라는 속성이 있어야합니다.
        return obj.owner == request.user
```
generic view는 적절한 개체 수준 사용 권한을 검사하지만 custom view를 작성하는 경우 개체 수준 사용 권한 검사를 직접 확인해야합니다. 객체 인스턴스가 있으면 뷰에서 `self.check_object_permissions(request, obj)`를 호출하여 그렇게 할 수 있습니다. 개체 수준의 권한 체크가 실패했을 경우,이 호출은 적절한 `APIException`을 송출하고, 그렇지 않은 경우는 단순히 반환됩니다.  
또한  generic view는 단일 모델 인스턴스를 검색하는 뷰의 오브젝트 레벨의 권한만을 체크합니다.
목록 뷰의 개체 수준 필터링이 필요한 경우는 별도로 쿼리 세트를 필터링해야합니다. 자세한 내용은 [filtering documentation](http://www.django-rest-framework.org/api-guide/filtering/) 참조

## Third party packages
다음 타사 패키지도 제공됩니다.

### Composed Permissions
[Composed Permissions](https://github.com/niwinz/djangorestframework-composed-permissions) 패키지는 작고 재사용 가능한 구성 요소를 사용하여 (논리 연산자를 사용하여) 복잡한 멀티 심도 권한 객체를 쉽게 정의하는 방법을 제공합니다.

### REST Condition
[REST Condition](https://github.com/caxap/rest_condition) 패키지는 복잡한 권한을 쉽고 편리하게 구축하기 위한 또 다른 확장 기능입니다. 확장 기능을 사용하면 권한을 논리 연산자와 결합 할 수 있습니다.

### DRY Rest Permissions
[DRY Rest Permissions](https://github.com/dbkaplan/dry-rest-permissions) 패키지는 개별 기본 및  custom 액션에 대해 서로 다른 권한을 정의하는 기능을 제공합니다. 이 패키지는 응용 프로그램의 데이터 모델에 정의 된 관계에서 파생 된 권한을 가진 애플리케이션 용으로 만들어져 있습니다. 또한 API serializer를 통해 클라이언트 응용 프로그램에 반환되는 권한 검사도 지원하고 있습니다. 또한 사용자마다 취득하는 데이터를 제한하기 위해 기본 및 custom 목록 액션에 권한을 추가도 지원합니다.

### Django Rest Framework Roles
[Django Rest Framework Roles](https://github.com/computer-lab/django-rest-framework-roles) 패키지를 사용하면 여러 유형의 사용자에 대해 API를 쉽게 매개 변수화 할 수 있습니다.

### Django Rest Framework API Key
[Django Rest Framework API Key](https://github.com/manosim/django-rest-framework-api-key) 패키지를 사용하면 서버에 대한 모든 요청에 ​​API 키 헤더가 필요함을 확인할 수 있습니다. 당신은 django 관리 인터페이스에서 생성 할 수 있습니다.
