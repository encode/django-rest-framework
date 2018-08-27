# Django REST Framework - Status Codes

---

_"418 I'm a teapot - Any attempt to brew coffee with a teapot should result in the error code "418 I'm a teapot". The resulting entity body MAY be short and stout."_  

_"418 저는 주전자입니다 - 주전자로 커피를 양조하려고하면 "418 나는 주전자입니다"라는 오류 코드가 나타납니다. 그 결과로 생성 된 실제 몸체는 짧고 튼튼 할 수 있다."_  

_— RFC 2324, Hyper Text Coffee Pot Control Protocol_

---

## Status Codes
응답에 베어 상태 코드를 사용하는 것은 좋지 않습니다. REST 프레임워크에는 더 많은 코드를 보다 명확하고 읽기 쉽게 만드는데 사용 할 수 있는 명명 된 상수 set이 포함되어 있습니다.

```python
from rest_framework import status
from rest_framework.response import Response

def empty_view(self):
    content = {'please move along': 'nothing to see here'}
    return Response(content, status=status.HTTP_404_NOT_FOUND)
```
`status` 모듈에 포함된 HTTP status code의 full set은 다음과 같습니다.  
모듈에는 status code가 주어진 범위에 있는지 테스트하기 위한 helper 함수 set가 포함되어 있습니다.

```python
from rest_framework import status
from rest_framework.test import APITestCase

class ExampleTestCase(APITestCase):
    def test_url_root(self):
        url = reverse('index')
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
```
HTTP status code의 올바른 사용법에 대한 자세한 내용은 [RFC 2616](https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html)와 [RFC 6585](https://tools.ietf.org/html/rfc6585)를 참조사헤요.

### Informational - 1xx
이 status code 클래스는 잠정적인 응답을 나타냅니다. 기본적으로 REST 프레임워크에는 1xx status code가 사용되지 않습니다.

```
HTTP_100_CONTINUE
HTTP_101_SWITCHING_PROTOCOLS
```

### Successful - 2xx
이 status code 클래스는 클라이언트 요청이 성공적으로 수신, 이해, 승인되었음을 나타냅니다.

```
HTTP_200_OK
HTTP_201_CREATED
HTTP_202_ACCEPTED
HTTP_203_NON_AUTHORITATIVE_INFORMATION
HTTP_204_NO_CONTENT
HTTP_205_RESET_CONTENT
HTTP_206_PARTIAL_CONTENT
HTTP_207_MULTI_STATUS
```

### Redirection - 3xx
이 status code 클래스는 요청을 수행하기 위해 사용자 에이전트가 추가 조치를 취해야 함을 나타냅니다.

```
HTTP_300_MULTIPLE_CHOICES
HTTP_301_MOVED_PERMANENTLY
HTTP_302_FOUND
HTTP_303_SEE_OTHER
HTTP_304_NOT_MODIFIED
HTTP_305_USE_PROXY
HTTP_306_RESERVED
HTTP_307_TEMPORARY_REDIRECT
```

### Client Error - 4xx
4xx 클래스의 status code는 클라이언트가 오류가 있는 것으로 보이는 경우를 위한 것입니다. HEAD request에 응답 할 때를 제외하고, 서버 SHOULD는 오류 상황에 대한 설명과 일시적인 것인지 지속적인 것인지를 포함한 엔티티를 포함해야합니다.

```
HTTP_400_BAD_REQUEST
HTTP_401_UNAUTHORIZED
HTTP_402_PAYMENT_REQUIRED
HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND
HTTP_405_METHOD_NOT_ALLOWED
HTTP_406_NOT_ACCEPTABLE
HTTP_407_PROXY_AUTHENTICATION_REQUIRED
HTTP_408_REQUEST_TIMEOUT
HTTP_409_CONFLICT
HTTP_410_GONE
HTTP_411_LENGTH_REQUIRED
HTTP_412_PRECONDITION_FAILED
HTTP_413_REQUEST_ENTITY_TOO_LARGE
HTTP_414_REQUEST_URI_TOO_LONG
HTTP_415_UNSUPPORTED_MEDIA_TYPE
HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
HTTP_417_EXPECTATION_FAILED
HTTP_422_UNPROCESSABLE_ENTITY
HTTP_423_LOCKED
HTTP_424_FAILED_DEPENDENCY
HTTP_428_PRECONDITION_REQUIRED
HTTP_429_TOO_MANY_REQUESTS
HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE
HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS
```

### Server Error - 5xx
숫자 "5"로 시작하는 response status code는 서버에 오류가 발생했거나 요청을 수행 할 수 없다는 것을 알고있는 경우를 나타냅니다. HEAD requset에 응답할 때를 제외하고, 서버 SHOULD 는 오류 상황에 대한 설명과 일시적인지 것인지 지속적인 것인지를 포함한 엔티티를 포함해야합니다.

```
HTTP_500_INTERNAL_SERVER_ERROR
HTTP_501_NOT_IMPLEMENTED
HTTP_502_BAD_GATEWAY
HTTP_503_SERVICE_UNAVAILABLE
HTTP_504_GATEWAY_TIMEOUT
HTTP_505_HTTP_VERSION_NOT_SUPPORTED
HTTP_507_INSUFFICIENT_STORAGE
HTTP_511_NETWORK_AUTHENTICATION_REQUIRED
```

### Helper functions
다음 helper 함수는 응답 코드의 범주를 식별하는데 사용할 수 있습니다.

```
is_informational()  # 1xx
is_success()        # 2xx
is_redirect()       # 3xx
is_client_error()   # 4xx
is_server_error()   # 5xx
```
