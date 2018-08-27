# Django REST Framework - Views

--- 

_"Django's class-based views are a welcome departure from the old-style views."_  

_"Django의 CBV는 구식 뷰에서 출발하는 것을 환영합니다."_  

_— Reinout van Rees_

---

## Class-based Views
REST 프레임워크는 Django의 `View` 클래스를 하위 클래스로 하는 `APIView`클래스를 제공합니다.  
`APIView`클래스는 다음과 같은 방식으로 일반 `View`클래스와 다릅니다.

- 핸들러 메서드에 전달 된 `Request`는 Django의 `HttpRequest` 인스턴스가 아닌 REST 프레임워크의 `request`인스턴스가 됩니다.
- 핸들러 메서드는 Django의 `HttpResponse` 대신 REST 프레임워크의 `Response`를 반환 할 수 있습니다. 뷰는 콘텐츠 협상을 관리하고 `response`에서 올바른 렌더러를 설정합니다.
- 모든 `APIException` 예외가 발견되면 적절한 `response`으로 조정됩니다.
- 들어오는 request가 인증이 된 request를 핸들러 메서드에 보내기 전에 적절한 권한과 `/` 또는 `throttle(제한)` 체크를 실행합니다.

`APIView` 클래스를 사용하는 것은 일반 `View`클래스를 사용하는 것과 거의 같습니다. 들어오는 request은 `.get()`이나 `.post()`와 같은 적절한 핸들러 메서드로 전달됩니다. 또한 API 정책의 다양한 측면을 제어하는 여러 속성을 클래스에 설정 할 수 있습니다.

예를 들어:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

class ListUsers(APIView):
    """
    View to list all users in the system.

    * 토큰 인증이 필요합니다.
    * 관리자만 view에 액서스 할 수 있습니다.
    """
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request, format=None):
        """
        모든 사용자 리스트를 반환합니다.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)
```

### API policy attributes(API 정책 속성)
다음 속성들은 API view의 플러그 가능한 부분을 제어합니다.  
`.renderer_classes`  
`.parser_classes`  
`.authentication_classes`  
`.throttle_classes`  
`.permission_classes`  
`.content_negotiation_class`  

### API policy instantiation methods(API 정책 인스턴스화 메서드)
다음 메서드들은 REST 프레임워크에서 다양한 플러그가 가능한 API 정책을 인스턴스화하는데 사용됩니다. 일반적으로 이러한 메서드를 재정의 할 필요는 없습니다.  
`.get_renderers(self)`  
`.get_parsers(self)`  
`.get_authenticators(self)`  
`.get_throttles(self)`  
`.get_permissions(self)`  
`.get_content_negotiator(self)`  
`.get_exception_handler(self)`  

### API policy implementation methods(API 정책 구현 방법)
다음 메서드는 핸들러 메서드에 전달하기 전에 호출됩니다.  
`.check_permissions(self, request)`  
`.check_throttles(self, request)`  
`.perform_content_negotiation(self, request, force=False)`  

### Dispatch methods (파견 메서드)
다음 메서드는 뷰의 `.dispatch()`메서드에 의해 직접 호출됩니다. 이 메서드들은 `.get()`, `.post()`, `put()`, `patch()` 및 `.delete()`와 같은 핸들러 메서드들을 호출하기 전후에 수행되어야하는 모든 조치들을 수행합니다.  

#### `.initial(self, request, *args, **kwargs)`
핸들러 메서드가 호출되기 전에 발생해야하는 모든 작업을 수행합니다. 이 메서드는 사용 권한 및 제한을 적용하고 콘텐츠 협상을 수행하는데 사용됩니다.  
일반적으로 이 메서드를 재정의 할 필요는 없습니다.

#### `.handle_exception(self, exc)`
핸들러 메서드에 의해 버려진 예외는 `Resopnse`인스턴스를 반환하거나 예외를 다시 발생시키는 이 메서드로 전달됩니다.  
기본 구현에서는 Django의 `Http404`와 `PermissionDenied`예외 뿐만 아니라 `rest_framework.exceptions.APIXeception`의 하위 클래스를 처리하고 적절한 오류 response를 반환합니다.  
API에서 반환하는 오류 response를 사용자 정의해야하는 경우 이 메소드를 서브 클래스화해야 합니다.

#### `.initialize_request(self, request, *args, **kwargs)`
핸들러 메소드에 전달 된 request 객체가 일반적인 Django `HttpRequest`가 아닌 `Request`의 인스턴스인지 확인합니다.  
일반적으로 이 메서드를 재정의 할 필요는 없습니다.  

#### `.finalize_response(self, request, response, *args, **kwargs)`
핸들러 메서드에서 반환 된 모든 `Response`객체가 내용 협상에 의해 결정된 대로 올바른 내용 유형으로 렌더링되도록 합니다.  
일반적으로 이 메서드는 재정의 할 필요는 없습니다.

---

### Function Based Views
_"Saying [that class-based views] is always the superior solution is a mistake."_  
_"[그 클래스 기반의 견해]가 항상 우월한 해결책은 실수라고 말하는 것입니다."_  

_— Nick Coghlan_  

REST 프레임워크를 사용하면 일반 FBV로 작업 할 수 있습니다. 그것은 간단한 Django `HttpRequest`가 아닌 `Request`의 인스턴스를 수신하고 Django `HttpResponse` 대신 `response`을 리턴 할 수 있도록 FBV를 래핑하는 간단한 데코레이터 세트를 제공하며, request가 처리됩니다.  

### @api_view()
**Signature**: `@api_view(http_method_names=['GET'], exclude_from_schema=False)`  
이 기능의 핵심은 `api_view`데코레이터(뷰가 응답해야하는 HTTP 메서드 리스트를 사용함)입니다. 예를 들어, 다음은 몇 가지 데이터를 수동으로 반환하는 아주 간단한 view를 작성하는 방법입니다.

```python
from rest_framework.decorators import api_view

@api_view()
def hello_world(request):
    return Response({"message": "Hello, world!"})
```
이 뷰는 [설정](http://www.django-rest-framework.org/api-guide/settings/)에 지정된 기본 렌더러, 파서, 인증 클래스 등을 사용합니다.  
기본적으로 `GET`메서드만 허용됩니다. 다른 메서드들은 "405 Method Not Allowed"로 응답합니다. 이 동작을 변경하려면 view에서 허용하는 방법을 지정하세요.

```python
@api_view(['GET', 'POST'])
def hello_world(request):
    if request.method == 'POST':
        return Response({"message": "Got some data!", "data": request.data})
    return Response({"message": "Hello, world!"})
```
`exclude_from_schema`인수를 사용하여 API 뷰를 [자동 생성 스키마(auto-generated schema)](http://www.django-rest-framework.org/api-guide/schemas/)에서 생략된 것으로 표시 할 수도 있습니다.

```python
@api_view(['GET'], exclude_from_schema=True)
def api_docs(request):
    ...
```

### API policy decorators
기본 설정을 재정의하기 위해 REST 프레임워크는 뷰에 추가 할 수 있는 일련의 추가 데코레이터를 제공합니다. 이들은 `@api_view`데코레이터 다음에 와야합니다. 예를 들어, [`throttle`](http://www.django-rest-framework.org/api-guide/throttling/)을 사용하여 특정 사용자가 하루에 한번만 호출 할 수 있도록 뷰를 만들려면 `@thottle_classes`데코레이터를 사용하여 `throttle` 클래스 목록을 전달하세요.

```python
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import UserRateThrottle

class OncePerDayUserThrottle(UserRateThrottle):
        rate = '1/day'

@api_view(['GET'])
@throttle_classes([OncePerDayUserThrottle])
def view(request):
    return Response({"message": "Hello for today! See you tomorrow!"})
```
이러한 데코레이터는 위에서 설명한 `APIView`하위 클래스에 설정된 특성에 해당합니다. 사용 가능한 데코레이터는 다음과 같습니다.  

- `@renderer_classes(...)`
- `@parser_classes(...)`
- `@authentication_classes(...)`
- `@throttle_classes(...)`
- `@permission_classes(...)` 
 
이러한 데코레이터 각각은 클래스의 `list`나 `tuple`인 단일 인수를 취합니다.
