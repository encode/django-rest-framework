# Django REST Framework - Returning URLs

---

_"The central feature that distinguishes the REST architectural style from other network-based styles is its emphasis on a uniform interface between components."_  

_"REST 아키텍처 스타일을 다른 네트워크 기반 스타일과 구별하는 핵심 기능은 구성 요소 간의 균일한 인터페리스에 중점을 둡니다."_  

_— Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures_

---

## Returning URLs
일반적으로 `/foobar`와 같은 상대URL를 반환하는 것이 아니라 `http://example.com/foobar`와 같이 웹 API에서 절대 URI를 반환하는 것이 좋습니다.  

이렇게 하는 이점은 다음과 같습니다.

- 이것이 더 명시적입니다.
- 당신의 API 클라이언트에 대한 작업을 적게 남겨둡니다.
- 네이티브 URI 유형이 없는 JSON과 같은 표현에서 문자열의 의미에 대한 모호성이 없습니다.
- 하이퍼링크를 사용하여 마크업 HTML 표현과 같은 작업을 쉽게 수행할 수 있습니다.

REST 프레임워크는 웹 API에서 절대 URI를 리턴하는 것을 보다 간단하게 해주는 두가지 유틸리티 함수를 제공합니다.  
사용자가 직접 사용하도록 요구할 필요는 없지만 사용자가 직접 입력하면 자체 설명 API가 출력을 자동으로 하이퍼링크로 연결할 수 있으므로 API를 훨씬 쉽게 찾을 수 있습니다.

### reverse
**Signature**: `reverse(viewname, *args, **kwargs)`  
[`django.urls.reverse`](https://docs.djangoproject.com/en/1.10/topics/http/urls/#reverse)와 동일한 동작을 하지만 호스트와 포트를 결정하기 위한 요청을 사용하여 정규화 된 URL을 반환합니다.  
함수에 대한 **키워드 인수로 request을 포함**해야합니다. 예:

```python
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from django.utils.timezone import now

class APIRootView(APIView):
    def get(self, request):
        year = now().year
        data = {
            ...
            'year-summary-url': reverse('year-summary', args=[year], request=request)
        }
        return Response(data)
```

### reverse_lazy

**Signature**: `reverse_lazy(viewname, *args, **kwargs)`  
`django.urls.reverse_lazy`와 동일한 동작을 하지만 호스트와 포트를 결정하기위한 요청을 사용하여 정규화 된 URL을 반환한다는 점만 다릅니다.  
`reverse` 함수와 마찬가지로 함수에 대한 **키워드 인수로 request를 포함**해야합니다. 예:

```
api_root = reverse_lazy('api-root', request=request)
```
