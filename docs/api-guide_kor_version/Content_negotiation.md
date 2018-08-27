# Django REST Framework - Content negotiation

---

_"HTTP has provisions for several mechanisms for "content negotiation" - the proce반s of selecting the best representation for a given response when there are multiple representations available."_  

_"HTTP는 "내용 협상 (content negotiation)"에 대한 몇 가지 메커니즘에 대한 규정을 제공합니다. 이는 여러 표현을 사용할 수 있는 경우 주어진 응답에 대한 최상의 표현을 선택하는 프로세스입니다."_  

_— RFC 2616, Fielding et al._

---

## Content negotiation
content negotiation은 클라이언트 또는 서버 환경 설정에 따라 클라이언트로 리턴할 수 있는 여러 표현 중 하나를 선택하는 프로세스입니다.

### Determining the accepted renderer
REST 프레임워크는 간단한 스타일의 content negotiation을 사용하여 사용 가능한 renderer. 각 렌더러의 우선 순위 및 클라이언트의 `Accept:` 헤더를 기반으로 클라이언트에 반환해야하는 미디어 유형을 결정합니다. 사용되는 스타일은 부분적으로 클라이언트 / 서버 중심적입니다.

1. 더 구체적인 미디어 유형은 덜 구체적인 미디어 유형보다 우선합니다.
2. 복수의 미디어 타입이 같은 특이성을 가지는 경우, 지정된 뷰에 대해서 설정된 렌더러의 순서에 따라 우선권이 주어집니다.

예를 들어, 다음 `Accept` 헤더가 제공됩니다.

```
application/json; indent=4, application/json, application/yaml, text/html, */*
```

각 미디어 유형의 우선 순위는 다음과 같습니다.

- `application/json; indent=4`
- `application/json`, `application/yaml` and `text/html`
- `*/*`

요청 된 뷰가 `YAML`과 `HTML`용 렌더러로만 구성된 경우 REST 프레임워크는 `renderer_classes` list 또는 `	DEFAULT_RENDERER_CLASSES` 설정에서 먼저 나열된 렌더러를 선택합니다.  

HTTP Accept 헤더에 대한 자세한 내용은 [`RFC 2616`](https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html)을 참조하십시오.

---

**Note** : 환경 설정에서 REST 프레임워크가 `"q"`값을 고려하지 않습니다. `"q"`값의 사용은 캐싱에 부정적인 영향을 주며 저자의 의견으로는 content negotiation에 불필요하고 복잡해지는 접근방식입니다.  

이는 HTTP 사양이 의도적으로 서버가 클라이언트 기반 환경설정에 대해 서버 기잔 환경설정에 가중치를 부여하는 방법을 명시하지 않기 때문에 유효한 접근 방식입니다.

---

## Custom content negotiation
REST 프레임워크에 대해 custom content negotiation scheme를 제공하는 것은 거의 불가능하지만 필요한 경우 그렇게 할 수 있습니다. custom content negotiation scheme를 구현하려면 `BaseContentNegotiation`을 오버라이드합니다.  

REST 프레임워크의 content negotiation 클래스는 요청에 대한 적절한 파서 및 응답에 적합한 렌더러 모두를 처리하므로 `.select_parser(request, parser)` 및 `.select_renderer(request, renderers, format_suffix)` 메서드를 모두 구현해야합니다.  

`select_parser()`메서드는 파서 인스턴스 중 하나를 사용 가능한 파서 목록에서 반환하거나 파서가 들어오는 요청을 처리 할 수 없는 경우 `None`을 반환해야합니다.  

`select_renderer()`메서드는 (renderer instance, media type)의 두 tuple을 반환하거나 `NotAcceptable` 예외를 발생시킵니다.

### Example
다음은 적절한 파서 또는 렌더러를 선택할 때 클라이언트 요청을 무시하는 custom content negotiation 클래스입니다.

```python
from rest_framework.negotiation import BaseContentNegotiation

class IgnoreClientContentNegotiation(BaseContentNegotiation):
    def select_parser(self, request, parsers):
        """
        Select the first parser in the `.parser_classes` list.
        """
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix):
        """
        Select the first renderer in the `.renderer_classes` list.
        """
        return (renderers[0], renderers[0].media_type)
```

### Setting the content negotiation
기본 content negotiation 클래스는 `DEFAULT_CONTENT_NEGOTIATION_CLASS`설정을 사용하여 전역으로 설정 할 수 있습니다. 예를 들어, 다음 설정은 예제 `IgnoreClientContentNegotitaion`클래스를 사용합니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'myapp.negotiation.IgnoreClientContentNegotiation',
}
```
`APIView` CBV를 사용하여 개별 view 또는 viewset에 사용 된 content negotiation을 설정할 수도 있습니다.

```python
from myapp.negotiation import IgnoreClientContentNegotiation
from rest_framework.response import Response
from rest_framework.views import APIView

class NoNegotiationView(APIView):
    """
    An example view that does not perform content negotiation.
    """
    content_negotiation_class = IgnoreClientContentNegotiation

    def get(self, request, format=None):
        return Response({
            'accepted media type': request.accepted_renderer.media_type
        })
```