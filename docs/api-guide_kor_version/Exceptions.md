# Django REST Framework - Exceptions

---

_"Exceptions… allow error handling to be organized cleanly in a central or high-level place within the program structure."_  

_"예외... 프로그램 구조 내의 중앙 또는 상위 위치에서 오류 처리를 명확하게 구성 할 수 있습니다."_  

_— Doug Hellmann, Python Exception Handling Techniques_
---

## Exceptions

### Exception handling in REST framework views
REST 프레임워크의 뷰는 다양한 예외를 처리하고 적절한 오류 응답을 반환합니다.  

처리되는 예외는 다음과 같습니다.  

- REST 프레임워크 내에서 발생하는 `APIException`의 서브클래스입니다.
- Django의 `Http404` exception.
- Django의 `PermissionDenied` exception.

각각의 경우에 REST 프레임워크는 적절한 상태 코드 및 내용 유형이 포함된 응답을 반환합니다. response 본문에는 오류의 성격에 관한 추가 세부 정보가 포함됩니다.  
대부분의 오류 응답에는 response 본문의 `detail`정보가 포함됩니다.  

예를 들어, 다음 요청은:

```
DELETE http://api.example.com/foo/bar HTTP/1.1
Accept: application/json
```
해당 리소스에서 `DELETE` 메서드가 허용되지 않는다는 오류 응답을 받을 수 있습니다.

```python
HTTP/1.1 405 Method Not Allowed
Content-Type: application/json
Content-Length: 42

{"detail": "Method 'DELETE' not allowed."}
```
유효성 검사 오류는 약간 다르게 처리되며 필드 이름을 응답의 키로 포함합니다. 유효성 검사 오류가 특정 필드에만 해당되지 않으면 `"non_field_errors"`키를 사용하거나 `NON_FIELD_ERRORS_KEY` 설정에 대해 설정된 문자열 값을 사용합니다.  
모든 유효성 검증 오류는 다음과 같습니다.

```python
HTTP/1.1 400 Bad Request
Content-Type: application/json
Content-Length: 94

{"amount": ["A valid integer is required."], "description": ["This field may not be blank."]}
```

### Custom exception handling
API view에서 발생한 예외를 response 객체로 변환하는 handler 함수를 만들어 custom exception를 구현할 수 있습니다. 이를 통해 API에서 사용되는 오류 응답 스타일을 제어할 수 있습니다.  

함수는 한쌍의 인수를 취해야하며, 첫번째는 처리할 예외이고, 두번째는 현재 처리중인 뷰와 같은 추가 context를 포함하는 dict입니다. exception handler 함수는 `Response` 객체를 반환하거나 예외를 처리 할 수 없는 경우 `None`을 반환해야합니다. handler가 `None`을 반환하면 예외가 다시 발생하고 Django는 표준 HTTP 500 'server error'응답을 반환합니다.  

예를 들어, 모든 오류 응답에 다음과 같이 HTTP 본문 코드에 HTTP 상태 코드가 포함되도록 할 수 있습니다.

```python
HTTP/1.1 405 Method Not Allowed
Content-Type: application/json
Content-Length: 62

{"status_code": 405, "detail": "Method 'DELETE' not allowed."}
```
response 스타일을 변경하기 위해 다음과 같은 custom exception handler를 작성 할 수 있습니다.

```python
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    return response
```
context 인수는 기본 handler에서 사용되지 않지만 exception handler가 `context['view']`로 액서스 할 수 있는 현재 처리중인 뷰와 같은 추가 정보를 필요로 할 때 유용할 수 있습니다.  
`EXCEPTION_HANDLER`설정 키를 사용하여 설정에서 exception handler를 구성해야합니다. 예:

```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'my_project.my_app.utils.custom_exception_handler'
}
```
지정하지 않으면 `EXCEPTION_HANDLER` 설정의 기본값은 REST 프레임워크에서 제공하는 표준 exception handler로 설정됩니다.

```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler'
}
```
exception handler는 발생하는 예외에 의해 생성 된 응답에 대해서만 호출됩니다. serializer 유효성 검사가 실패 할 때 generic view에서 반환되는 `HTTP_400_BAD_REQUEST`응답과 같이 뷰에서 직접 반환 된 응답에는 사용되지 않습니다.

---

## API Reference

### APIException
**Signature**: `APIException()`  
`APIView`클래스 또는 `@api_view`내부에서 발생한 모든 예외에 대한 기본 클래스입니다.  
custom exception을 제공하려면, `APIException`을 서브클래스화하고 클래스의 `.status_code`, `.default_detail` 및 `default_code`속성을 설정하세요.  
예를 들어, API가 가끔 도달 할 수 없는 제3자 서비스에 의존하는 경우, "503 Service Unavailable" HTTP response 코드에 대한 예외를 구현할 수 있습니다. 우리는 이렇게 할 수 있습니다.

```python
from rest_framework.exceptions import APIException

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'
```

#### Inspecting API exceptions
API exception을 검사하는데 사용할 수 있는 여러 속성이 있습니다. 이를 사용하여 프로젝트에 대한 custom exception를 빌드 할 수 있습니다.  
사용 가능한 속성 및 메서드는 다음과 같습니다.

- `.detail` : 오류의 텍스트 설명을 리턴합니다.
- `.get_codes()` : 오류의 코드 식별자를 반환합니다.
- `.get_full_details()` : 텍스트 설명과 코드 식별자를 반환합니다.  

대부분의 경우 오류 세부 사항은 간단한 항목입니다.

```python
>>> print(exc.detail)
You do not have permission to perform this action.
>>> print(exc.get_codes())
permission_denied
>>> print(exc.get_full_details())
{'message':'You do not have permission to perform this action.','code':'permission_denied'}
```
유효성 검사 오류의 경우 오류 세부 정보는 list나 dict입니다.

```python
>>> print(exc.detail)
{"name":"This field is required.","age":"A valid integer is required."}
>>> print(exc.get_codes())
{"name":"required","age":"invalid"}
>>> print(exc.get_full_details())
{"name":{"message":"This field is required.","code":"required"},"age":{"message":"A valid integer is required.","code":"invalid"}}
```

### ParseError
**Signature**: `ParseError(detail=None, code=None)`  
`request.data`에 엑서스 할 때 request에 잘못된 데이터가 포함 된 경우 발생합니다.  
기본적으로 이 예외는 HTTP status code "400 Bad Request"로 응답합니다.

### AuthenticationFailed
**Signature**: `AuthenticationFailed(detail=None, code=None)`  
들어오는 request에 잘못된 인증이 포함될 떄 발생합니다.  
기본적으로 이 예외로 인해 HTTP status code "401 Unauthenticated"가 반환되지만, 사용중인 인증 방식에 따라 "403 Forbidden" 응답이 발생할 수도 있습니다. 자세한 내용은 [인증 문서](http://www.django-rest-framework.org/api-guide/authentication/)를 참조하세요.

### NotAuthenticated
**Signature**: `NotAuthenticated(detail=None, code=None)`  
인증되지 않은 요청이 권한 검사에 실패하면 발생합니다.  
기본적으로 이 예외로 인해 HTTP status code "401 Unauthenticated"가 반환되지만 사용중인 인증 방식에 따라 "403 Forbidden"응답이 발생 할 수도 있습니다. 자세한 내용은 [인증 문서](http://www.django-rest-framework.org/api-guide/authentication/)를 참조하세요.

### PermissionDenied
**Signature**: `PermissionDenied(detail=None, code=None)`  
인증 된 요청이 권한 검사에 실패하면 발생합니다.  
기본적으로 이 예외는 HTTP status code "403 Forbidden"으로 응답하니다.

### NotFound
**Signature**: `NotFound(detail=None, code=None)`  
주어진 URL에 resource가 없을 때 발생합니다. 이 예외는 표준 `Http404` Django exception과 동일합니다.  
기본적으로 이 예외는 HTTP status code "404 Not Found"으로 응답합니다.

### MethodNotAllowed
**Signature**: `MethodNotAllowed(method, detail=None, code=None)`  
뷰의 handler 메서드에 매핑되지 않는 들어오는 request가 발생했을 떄 발생합니다.  
기본적으로 이 예외는 HTTP status code "405 Method Not Allowed"로 응답합니다.

### NotAcceptable
**Signature**: `NotAcceptable(detail=None, code=None)`  
사용 가능한 randerer에서 만족 할 수 없는 `Accept`헤더로 들어오는 request가 발생할때 발생합니다.  
기본적으로 이 예외는 HTTP status code "406 Not Acceptable"으로 응답합니다.

### UnsupportedMediaType
**Signature**: `UnsupportedMediaType(media_type, detail=None, code=None)`  
`request.data`에 엑서스 할 때 request 데이터의 내용 유형을 처리 할 수 있는 parser가 없는 경우 발생합니다.  
기본적으로 이 예외는 HTTP status code "415 Unsupported Media Type"으로 응답합니다.

### Throttled
**Signature**: `Throttled(wait=None, detail=None, code=None)`  
들어오는 request가 throttle 검사에 실패하면 발생합니다.  
기본적으로 이 예외는 HTTP status code "429 Too Many Requests"으로 응답합니다.

### ValidationError
**Signature**: `ValidationError(detail, code=None)`  
`ValidationError` 예외는 다른 `APIException`클래스와 약간 다릅니다.  

- `detail` 인수는 필수입니다. 선택사항이 아닙니다.
- `detail`인수는 오류 세부 사항 list 또는 dict 일 수 있으며, 중첩된 데이터 구조 일 수도 있습니다.
- 규약에 따라 serializer 모듈을 가져와 정규화 된 `ValidationError` 스타일을 사용하여 Django의 기본 유효성 검사 오류와 구별해야합니다. 예: `raise serializers.ValidationError('이 필드는 정수(Integer)값이어야 합니다.')`  

`ValidationError` 클래스는 serializer 및 필드 유효성 검사 및 유효성 검사기 클래스에 사용해야합니다. 또한 `raise_exception` 키워드 인수로 `serializer.is_valid`를 호출 할 때 발생합니다.

```
serializer.is_valid(raise_exception=True)
```
generic view는 `raise_exception=True`플래그를 사용합니다. 즉, API에서 유효성 검증 오류 응답의 스타일을 대체할 수 있습니다. 이렇게 하려면 위에서 설명한대로 custom exception handler를 사용하세요.  
기본적으로 이 예외는 HTTP status code "400 Bad Request"으로 응답합니다.
