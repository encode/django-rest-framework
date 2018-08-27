# Django REST Framework - Throttling

---

_"HTTP/1.1 420 Enhance Your Calm"_  

_Twitter API rate limiting response_

---

## Throttling (제한)
Throttling은 request가 승인되어야하는지 여부를 결정한다는 점에서 permissions와 유사합니다. Throttling은 임시상태를 나타내며 클라이언트가 API에 대해 수행 할 수 있는 request 빈도수를 제어하는데 사용됩니다.  
permissions과 마찬가지로, 여러 Throttle을 사용할 수 있습니다. API에는 인증되지 않은 요청에 대해 제한적으로 Throttle과 인증 된 요청에 대한 제한적인 Throttle이 있을 수 있습니다.  
특정 서비스가 특히 리소스를 잡아먹기 때문에 API의 다양한 부분에 다른 제약을 부과해야하는 경우, 여러 throttle을 사용하는 다른 시나리오가 있습니다.  
버스트 빈도수 제한와  지속적인 빈도수 제한을 동시에 적용하려는 경우, 여러 throttle을 사용할 수 있습니다. 예를 들어, 분당 최대 60개의 요청과 하루에 1000개의 요청으로 사용자를 제한 할 수 있습니다.  
throttle은 반드시 rate 제한 요청을 참조하는 것은 아닙니다. 예를 들어, 스토리지 서비스는 대역폭에 대해 조정해야 할 수고 있으며, 유료 데이터 서비스는 액서스되는 특정 레코드 수에 대해 조정할 수 있습니다.

### How throttling is determined
사용 권한 및 인증과 마찬가지로 REST 프레임워크의 Throttling은 항상 클래스 목록으로 정의됩니다.  
뷰의 본문을 실행하기 전에 list의 각 throttle이 점검됩니다. throttle 확인이 실패하면 `exceptions.Throttled`예외가 발생하고, 뷰 본문은 실행되지 않습니다.

### Setting the throttling policy
기본 throttling 정책은 `DEFAULT_THROTTLE_CLASSES`와 `DEFAULT_THROTTLE_RATES` 설정을 사용하여 전역으로 설정할 수 있습니다. 예를 들면.

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}
```
`DEFAULT_THROTTLE_RATES`에 사용 된 rate에는 throttle 기간으로 `second`, `minute`, `hour`, `day`이 포함 될 수 있습니다.  
또한 APIView CBV를 사용하여 뷰 단위 또는 뷰 단위별 조절 정책을 설정할 수 있습니다.

```python
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

class ExampleView(APIView):
    throttle_classes = (UserRateThrottle,)

    def get(self, request, format=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)
```
또는 FBV와 함께 `@api_view`데코레이터를 사용하는 경우

```python
@api_view(['GET'])
@throttle_classes([UserRateThrottle])
def example_view(request, format=None):
    content = {
        'status': 'request was permitted'
    }
    return Response(content)
```

### How clients are identified(클라이언트 식별 방법)  
`X-Forwarded_For`와 `Remote-Addr` HTTP 헤더는 throttling을 위해 클라이언트  IP주소를 고유하게 식별하는데 사용됩니다.  
`X-Forwarded_For`헤더가 있으면 사용되고, 없으면 `Remote-Addr` 헤더 값이 사용됩니다.  
고유한 클라이언트 IP주소를 엄격하게 식별해야하는 경우, 우선 `NUM-PROXIES`설정을 하여 API가 실행되는 응용 프로그램 프록시의 수를 구성해야 합니다. 이 설정은 0 이상의 정수이어야 합니다. 0 이 아닌 값으로 설정된 경우,  클라이언트 IP는 응용 프로그램 프록시 IP 주소가 먼저 제외되면 `X-Forwarded-For` 헤더의 마지막 IP 주소로 식별됩니다. 0 으로 설정하면 `Remote-Addr`헤더가 항상 식별 IP주소로 사용됩니다.  
`NUM_PROXIES`설정을 구성하면 고유한 `NAT'd` 게이트웨이 뒤에 있는 모든 클라이언트가 단일 클라이언트로 처리 된다는 것을 이해하는 것이 중요합니다.  
`X-Forwarded-For`헤더의 작동 방식 및 원격 클라이언트 IP 식별 방법에 대한 자세한 내용은 [여기](http://oxpedia.org/wiki/index.php?title=AppSuite:Grizzly#Multiple_Proxies_in_front_of_the_cluster)를 참조하세요.

### Setting up the cache
REST 프레임워크가 제공하는 throttle 클래스는 Django의 캐시 백엔드를 사용합니다. 적절한 [캐시 설정](https://docs.djangoproject.com/en/1.10/ref/settings/#caches)을 지정했는지 확인해야합니다. `LocMemCache`백엔드의 기본값은 간단한 설정으로 괜찮습니다. 자세한 내용은 [cache documentation](https://docs.djangoproject.com/en/1.10/topics/cache/#setting-up-the-cache)을 참조하세요.  
`default`가 아닌 캐시를 사용해야하는 경우, custom throttle 클래스를 만들고 캐시 속성을 설정하면 됩니다. 예를 들어:

```python
class CustomAnonRateThrottle(AnonRateThrottle):
    cache = get_cache('alternate')
```
`DEFAULT_THROTTLE_CLASSES` 설정 키 또는 `throttle_classes` 뷰 속성을 사용하여 custom throttle 클래스를 기억해야만 합니다.

## API Reference

### AnonRateThrottle
`AnonRateThrottle`은 인증되지 않은 사용자만 차단합니다. 들어오는 request의 IP 주소는 제한할 고유 키를 생성하는데 사용됩니다.  
허용 된 request 등급은 다음 중 하나(선호도순)로 결정됩니다.

- 클래스의 `rate` property는 `AnonRateThrottle`을 오버라이드하고 property를 설정하여 제공 될 수 있다.
- `DEFAULT_THROTTLE_RATES ['anon']` 설정입니다.  

`AnonRateThrottle`는 알 수 없는 출처에서의 request의 빈도수를 제한하려는 경우에 적합합니다.

### UserRateThrottle
`UserRateThrottle`은 API를 통해 주어진 request rate로 사용자를 제한합니다. user ID는 제한할 고유 키를 생성하는데 사용됩니다. 인증되지 않은 request는 들어오는 request의  IP 주소에 고유한 제한 키를 다시 생성하여 걸러냅니다.  
허용 된 request rate는 다음 중 하나(선호도 순)로 결정됩니다.  

- 클래스의 `rate`속성은 `UserRateThrottle`을 오버라이드하고 property를 설정하여 제공 될 수 있습니다.
- `DEFAULT_THROTTLE_RATES ['anon']` 설정입니다.  

API에는 동시에 여러 `UserRAteThrottles`이 있을 수 있습니다. 이렇게 하려면 `UserRateThrottle`을 무시하고 각 클래스에 대해 고유한 `scope`(범위)를 설정하세요.  
예를 들어, 여러 사용자 throttle rate는 다음 클래스를 사용하여 구현할 수 있습니다.

```python
class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'
```
...그리고 다음 설정입니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': (
        'example.throttles.BurstRateThrottle',
        'example.throttles.SustainedRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'burst': '60/min',
        'sustained': '1000/day'
    }
}
```
`UserRateThrottle`은 사용자별로 간단한 전역 rate를 원할 때 적합합니다.

### ScopedRateThrottle
`ScopeRateThrottle`클래스를 사용하여 API의 특정 부분에 대한 액서스를 제한 할 수 있습니다. 이 throttle은 액서스되는 뷰에 `.throttle_scope`속성이 포함 된 경우에만 적용됩니다. 고유한 throttle 키는 request의 "scope"를 고유한 user ID 또는 IP 주소와 연결하여 형성합니다.  
허용 된 request rate는 request "scope"의 키를 사용하여 `DEFAULT_THROTTLE_RATES`설정에 의해 결정됩니다.  
예를 들어, 다음의 뷰가 주어진 경우...

```python
class ContactListView(APIView):
    throttle_scope = 'contacts'
    ...

class ContactDetailView(APIView):
    throttle_scope = 'contacts'
    ...

class UploadView(APIView):
    throttle_scope = 'uploads'
    ...
```
...그리고 다음 설정입니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'contacts': '1000/day',
        'uploads': '20/day'
    }
}
```
`ContactListView` 또는 `ContactDetailView`에 대한 사용자 요청은 하루에 총 1000 개의 요청으로 제한됩니다. `UploadView`에 대한 사용자 요청은 하루에 20 건으로 제한됩니다.

## Custom throttles
custom throttle을 만들려면 `BaseThrottle`을 재정의하고 `.allow_request(self, request, view)`를 구현하십시오. 이 메소드는 요청을 허용해야하는 경우 `True`를 반환하고 그렇지 않으면 `False`를 반환해야합니다.  
선택적으로 `.wait()` 메서드를 재정의 할 수도 있습니다. 구현 된 경우 `.wait()`는 다음 요청을 시도하기 전에 기다리는 권장 시간(초)을 반환하거나 `None`을 반환해야합니다. `.wait()` 메서드는 `.allow_request()`가 이전에 `False`를 반환 한 경우에만 호출됩니다.  
`.wait()` 메서드가 구현되고 요청이 제한되면 `Retry-After` 헤더가 응답에 포함됩니다.

### Example
다음은 10의 요청마다 1을 무작위로 조절하는 rate throttle의 예입니다.

```python
import random

class RandomRateThrottle(throttling.BaseThrottle):
    def allow_request(self, request, view):
        return random.randint(1, 10) != 1
```
