# Django REST Framework - Responses

--- 

_"Unlike basic HttpResponse objects, TemplateResponse objects retain the details of the context that was provided by the view to compute the response. The final output of the response is not computed until it is needed, later in the response process."_  

_"기본 HttpResponse 객체와 달리 TemplateResponse 객체는 응답을 계산하기 위해 뷰에서 제공한 컨텍스트의 세부 정보를 유지합니다. response의 최종 출력은 나중에 응답 프로세스에서 필요할 때까지 계산되지 않습니다."_  

_— Django documentation_

## Responses
REST 프레임워크는 클라이언트 요청에 따라 여러 콘텐츠 형식으로 렌더링 할 수 있는 콘텐츠를 반환할 수 있는 `Response` 클래스를 제공하여 HTTP 콘텐츠 협상을 지원합니다.  
`response` 클래스는 Django의 `SimpleTemplateResponse`하위 클래스입니다. `response`객체는 Python 기본 요소로 구성되어야 하는 데이터로 초기화됩니다. 그런 다음 REST 프레임워크는 표준  HTTP 내용 협상을 사용하여 최종 응답 내용을 렌더링하는 방법을 결정합니다.  
`Response` 클래스를 사용할 필요는 없으며, 필요한 경우 일반 `HttpResponse`나 `StreamingHttpResponse` 객체를 뷰에서 반환 할 수도 있습니다. `Response`클래스를 사용하면 여러가지 형식으로 렌더링 할 수 있는 컨텐츠 협상 웹 API 응답을 반환하기에 더 좋은 인터페이스만 제공됩니다.  
어떤 이유로든 REST 프레임워크를 많이 사용자 정의하지 않으려면 `Response`객체를 반환하는 뷰에 항상 `APIView`클래스나 `@api_view`함수를 사용해야 합니다. 이렇게하면 뷰에서 내용협상을 수행하고 응답에 적합한 렌더러를 선택하여 뷰에 반환 할 수 있습니다.

---

## Creating responses

### Response()
**Signature** : `Response(data, status=None, template_name=None, headers=None, content_type=None)`  
일반 `HttpResponse`개체와 달리 렌더링 된 콘텐츠로 `Response` 개체를 인스턴스화하지 않습니다. 대신 기존의 파이썬으로 구성된 렌더링되지 않은 데이터를 전달합니다.  
`Response`클래스에서 사용하는 렌더러는 Django모델 인스턴스와 같은 복잡한 데이터 유형을 기본적으로 처리 할 수 없으므로 `Response`객체를 만들기 전에 데이터를 기본 데이터 유형으로 serializer해야 합니다.  
REST 프레임워크의 `Serializer`클래스를 사용하여 데이터를 serializer를 수행하거나 custom serializer를 사용할 수 있습니다.  

Arguments:  

- `data`: response의 serializer 된 데이터입니다.
- `status`: response의 상태 코드입니다. 기본값은 200입니다. [status codes](http://www.django-rest-framework.org/api-guide/status-codes/) 참조
- `template_name`: `HTMLRenderer`가 선택된 경우 사용할 템플릿 이름입니다.
- `headers`: 응답에 사용할 HTTP 헤더 dict입니다.
- `content_type`: 응답의 내용 유형입니다. 일반적으로 콘텐츠 협상에 따라 렌더러에서 자동으로 설정되지만 콘텐츠 유형을 명시적으로 지정해야하는 경우가 있습니다.

---

## Attributes

### .data
`Request` 객체의 렌더링되지 않은 내용입니다.

### .status_code
HTTP 응답의 숫자 상태 코드입니다.

### .content
`response`의 렌더링 된 내용입니다. `.content`에 액서스하려면 먼저 `.render()`메서드를 호출해야 합니다.

### .template_name
`template_name`이 제공된 경우. `HTTPRenderer`나 다른 custom 템플릿 렌더러가 응답에 대해 허용된 렌더러인 경우에만 필요합니다.

### .accepted_renderer
응답을 렌더링하는데 사용되는 렌더러 인스턴스입니다.  
뷰에서 응답이 반환되기 직전에 `APIView`나 `@api_view`에 의해 자동으로 설정됩니다.

### .accepted_media_type
콘텐츠 협상 단계에서 선택한 미디어 유형입니다.  
뷰에서 응답이 반환되기 직전에 `APIView`나 `@api_view`에 의해 자동으로 설정됩니다.

### .renderer_context
렌더러의 `.render()`메소드에 전달 될 추가 컨텍스트 정보의 dict입니다.
뷰에서 응답이 반환되기 직전에 `APIView`나 `@api_view`에 의해 자동으로 설정됩니다.

## Standard HttpResponse attributes
`Response`클래스는 `SimpleTemplateResponse`를 확장하고 모든 일반적이니 특성과 메서드를 response에서도 사용할 수 있습니다. 예를 들어 표준방식으로 response에 헤더를 설정 할 수 있습니다.

```python
response = Response()
response['Cache-Control'] = 'no-cache'
```

### .render()
**Signature**: `.render()`  
다른 `TemplateResponse`와 마찬가지로 이 메소드는 응답의 serializer 된 데이터를 최종 response 컨텐츠로 렌더링하기 위해 호출됩니다. `.render()`가 호출되면 `accept_renderer`인스턴스에서 `.render (data, accepted_media_type, renderer_context)` 메서드를 호출 한 결과로 response 내용이 설정됩니다.  
일반적으로 Django의 표준 응답주기에 의해 처리되므로 `.render()`를 직접 호출 할 필요가 없습니다.
