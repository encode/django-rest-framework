# Django REST Framework - Renderers

---

_"Before a TemplateResponse instance can be returned to the client, it must be rendered. The rendering process takes the intermediate representation of template and context, and turns it into the final byte stream that can be served to the client."_  

_"TemplateResponse 인스턴스가 클라이언트에 반환되기 전에 렌더링 되어야 합니다. 렌더링 프로세스는 템플릿과 컨텍스트의 중간 표현을 가져 와서 클래이언트에 제공 할 수 있는 최종 바이트 스트림으로 바꿉니다."_  

_— Django documentation_
  
---

## Renderers
REST 프레임워크에는 다양한 미디어 타입의 response를 반환할 수 있는 여러가지 `Renderer`클래스가 포함되어 있습니다. 또한 custom renderer를 정의할 수 있으므로 자신의 미디어 타입을 유연하게 디자인 할 수 있습니다.

### How the renderer is determined
뷰에 대한 유혀한 renderer set은 항상 클래스의 list로 정의됩니다. 뷰가 입력되면 REST 프레임워크는 들어오는 request에 대한 내용 협상을 수행하고, request를 만족시키는데 가장 적합한 renderer를 결정합니다.  
콘텐츠 협상의 기본 프로세스는 request의 `Accept`헤더를 조사하여 response에서 예상하는 미디어 타입을 판별하는 것입니다. 선택적으로, URL의  form suffixes를 사용하여 명시적으로 특정 표현을 요청할 수 있습니다. 예를 들어 URL `http://example.com/api/users_count.json`은 항상 JSON 데이터를 반환하는 엔드포인트 일 수 있습니다.  
더 자세한 내용은 [content negotiation](http://www.django-rest-framework.org/api-guide/content-negotiation/)을 참조하세요.

### Setting the renderers
기본 renderer set은 `DEFAULT_RENDERER_CLASSES` 설정을 사용하여 전역으로 설정할 수 있습니다. 예를 들어, 다음 설정은 `JSON`을 기본 미디어 타입으로 사용하며 자체 기술 API도 포함됩니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}
```
`APIView` CBV를 사용하여 개별 view나 viewset에 사용되는 renderer를 설정할 수도 있습니다.

```python
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

class UserCountView(APIView):
    """
    A view that returns the count of active users in JSON.
    """
    renderer_classes = (JSONRenderer, )

    def get(self, request, format=None):
        user_count = User.objects.filter(active=True).count()
        content = {'user_count': user_count}
        return Response(content)
```
또는 FBV의 뷰와 함께 `@aip_view`데코레이터를 사용하는 경우

```python
@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def user_count_view(request, format=None):
    """
    A view that returns the count of active users in JSON.
    """
    user_count = User.objects.filter(active=True).count()
    content = {'user_count': user_count}
    return Response(content)
```

### Ordering of renderer classes
API의 Renderer 클래스를 지정하여 각 미디어 타입에 할당 할 우선 순위를 생각할 때 중요합니다. 클라이언트가 `Accept: */*` 헤더를 보내는 것과 `Accept` 헤더를 포함하지 않는 것과 같이 받아 들일 수 있는 표현은 클라이언트가 명시하지 않으면 REST 프레임워크는 list에서 response에 사용할 첫번째 renderer를 선택합니다.  
예를 들어 API가 JSON response과 HTML browsable API를 제공하는 경우, `Accept` 헤더를 지정하지 않은 클라이언트에 `JSON` 응답을 보내려면 `JSONRenderer`를 기본 renderer로 설정하는 것이 좋습니다.  
API에 요청에 따라 일반 웹 페이지와 API 응답을 모두 제공 할 수있는 view가 포함되어있는 경우, [깨진 승인 헤더](http://www.newmediacampaigns.com/blog/browser-rest-http-accept-headers)를 보내는 오래된 브라우저에서 제대로 작동하려면 `TemplateHTMLRenderer`를 기본 렌더러로 설정하는 것이 좋습니다.

---

## API Reference

### JSONRenderer
utf-8 인코딩을 사용하여 request 데이터를 `JSON`으로 렌더링합니다.  
기본 스타일은 유니코드 문자를 포함하고 불필요한 공백 없이 콤팩트 스타일을 사용하여 response를 렌더링하는 것입니다.

```python
{"unicode black star":"★","value":999}
```
클라이언트는 `indent`미디어 타입 parameter를 추가로 포함할 수 있습니다. 이 경우 반환 된 JSON은 들여쓰기 됩니다. 예: `Accept: application/json; indent=4`

```python
{
    "unicode black star": "★",
    "value": 999
}
```
기본 JSON 인코딩 스타일은 `UNICODE_JSON`과 `COMPACT_JSON` 설정 키를 사용하여 변경할 수 있습니다.  
**.media_type**: `application/json`  
**.format**: `'.json'`  
**charset**: `None`

### TemplateHTMLRenderer
Django의 표준 템플릿 렌더링을 사용하여 데이터를 HTML으로 렌더링합니다. 다른 renderer와 달리 `Response`에 전달 된 데이터는 serializer 할 필요가 없습니다. 또한 다른 renderer와 달리 `Response`를 만들 때 `template_name`인수를 포함 할 수 있습니다.  
TemplateHTMLRenderer는 `response,data`를 컨텍스트 dict로 사용하여 `RequestContext`를 만들고 컨텍스트를 렌더링하는데 사용할 템플릿 이름을 결정합니다.  
템플릿 이름은 (우선 순위에 따라) 다음과 같이 결정됩니다:  
1. 명시적으로 `template_name`인수는 response에 전달됩니다.
2. 이 클래스는 명시적인  `.template_name` 속성이 설정됩니다.
3. `view.get_template_names()`를 호출 한 결과를 반환합니다.  

`TemplateHTMLRenderer`를 사용하는 view의 예:

```python
class UserDetail(generics.RetrieveAPIView):
    """
    A view that returns a templated HTML representation of a given user.
    """
    queryset = User.objects.all()
    renderer_classes = (TemplateHTMLRenderer,)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return Response({'user': self.object}, template_name='user_detail.html')
```
`TemplateHTMLRenderer`으로 REST 프레임워크를 사용하여 일반 HTML 페이지를 리턴하거나 HTML 및 API 응답을 단일 엔드포인트에서 리턴하도록 사용할 수 있습니다.  
`TemplateHTMLRenderer`를 사용하는 웹 사이트를 구축하는 경우 `TemplateHTMLRenderer`를 `renderer_classes` 목록의 첫 번째 클래스로 나열하는 것이 좋습니다. 이렇게하면 잘못 형성된 `ACCEPT:` 헤더를 보내는 브라우저에 대해서도 우선 순위가 지정됩니다.  
`TemplateHTMLRenderer`사용에 대한 추가 예제는 [HTML & Forms Topic Page](http://www.django-rest-framework.org/topics/html-and-forms/)를 참조하세요.  

**.media_type**: `text/html`  
**.format**: `'.html'`  
**.charset**: `utf-8`  
참조 : `StaticHTMLRenderer`

### StaticHTMLRenderer
단순히 미리 렌더링 된 HTML을 반환하는 단순한 renderer입니다. 다른 렌더러와 달리 response 객체에 전달 된 데이터는 반환 할 내용을 나타내는 문자열이어야 합니다.  
`StaticHTMLRenderer`를 사용하는 view의 예:

```python
@api_view(('GET',))
@renderer_classes((StaticHTMLRenderer,))
def simple_html_view(request):
    data = '<html><body><h1>Hello, world</h1></body></html>'
    return Response(data)
```
`StaticHTMLRenderer`는 REST 프레임워크를 사용하여 일반 HTML페이지를 리턴하거나 HTML및 API 응답을 단일 엔드포인트에서 리턴하도록 사용할 수 있습니다.  

**.media_type**: `text/html`  
**.format**: `'.html'`  
**.charset**: `utf-8`  
참조 : `TemplateHTMLRenderer`

### BrowsableAPIRenderer
Browsable API를 위해 데이터를 HTML으로 렌더링합니다.
![](./images/BrowsableAPIRenderer.png)  
이 renderer는 가장 우선순위가 높은 다른 renderer를 셜정하고 이를 사용하여 HTML 페이지 내에 API 스타일 response를 표시합니다.  

**.media_type**: `text/html`  
**.format**: `'.api'`  
**.charset**: `utf-8` 
**.template**: `'rest_framework/api.html'`  

#### Customizing BrowsableAPIRenderer
기본적으로 response content는 `BrowsableAPIRenderer`와 별도로 우선 순위가 가장 높은 renderer로 렌더링 됩니다. 이 동작을 custom 해야하는 경우 (ex: HTML을 기본 리턴 형식으로 사용하고 browsable API에서 JSON을 사용하는 경우) `get_default_renderer()` 메서드를 대체하서 이를 수행 할 수 있습니다. 예:

```python
class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    def get_default_renderer(self, view):
        return JSONRenderer()
```

### AdminRenderer
관리자와 같은 디스플레이를 위해 데이터를 HTML으로 렌더링합니다.
![](./images/AdminRenderer.png)

이  renderer는 데이터 관리를 위한 사용자에게 친숙한 인터페이스를 제공해야하는 CRUD 스타일 웹 API에 적합합니다.  
>CRUD : Create(생성), Read(읽기), Update(갱신), Delete(삭제)

HTML 폼이 제대로 지원하지 못하기 때문에 중첩 된 뷰 또는 입력을 위해 serializer를 나열한 뷰는 `AdminREnderer`와 잘 작동하지 않습니다.  
**Note**: `AdminRenderer`는 올바르게 구성된 `URL_FIELD_NAME`(기본적으로 url)속성이 데이터에 있는 경우에만 detail 페이지에 대한 링크를 포함할 수 있습니다. `HyperlinkedModelSerializer`의 경우지만, `ModelSerializer` 또는 일반 Serializer 클래스의 경우 필드를 명시적으로 포함해야합니다. 예를 들어 여기서는 `get_absolute_url` 모델을 사용합니다.

```python
class AccountSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Account
```
**.media_type**: `text/html`  
**.format**: `'.admin'`  
**.charset**: `utf-8`  
**.template**: `'rest_framework/admin.html'`

### HTMLFormRenderer
serializer에서 반환된 데이터를 HTML from으로 렌더링합니다. 이 renderer의 출력에는  포함된 `<form>`태크, 숨겨진 `CSRF`입력이나 `submit`버튼이 포함되지 않습니다.  
이 renderer는 직접 사용하기 위한 것이 아니며, serializer 인스턴스를  `renderer_form` 템플릿 태그에 전달하여 템플릿에서 대신 사용할 수 있습니다.  

```python
{% load rest_framework %}

<form action="/submit-report/" method="post">
    {% csrf_token %}
    {% render_form serializer %}
    <input type="submit" value="Save" />
</form>
```
더 자세한 내용은 [HTML & Forms](http://www.django-rest-framework.org/topics/html-and-forms/)를 참조하세요.  

**.media_type**: `text/html`  
**.format**: `'.form'`  
**.charset**: `utf-8`  
**.template**: `'rest_framework/horizontal/form.html'`  

### MultiPartRenderer
이 renderer는 HTML 다중 파트 form 데이터를 렌더링하는데 사용됩니다. response renderer로는 적합하지 않지만 대신 REST 프레임워크의 [테스트 클라이언트 및 테스트 request 팩토리](http://www.django-rest-framework.org/api-guide/testing/)를 사용하여 테스트 request를 만드는데 사용됩니다.  

**.media_type**: `multipart/form-data; boundary=BoUnDaRyStRiNg`  
**.format**: `'.multipart'`  
**.charset**: `utf-8`  

---

## Custom renderers
custom renderer를 구현하려면 `BaseRenderer`를 재정의하고, `.media_type`와 `.format`속성을 설정하고 `.render(self, data, media_type=None, renderer_context=None)` 메서드를 구현해야 합니다.  
메서드는 HTTP response의 본문으로 사용될 바이트 테스트를 반환해야합니다.  
`render()`메서드에 전달 된 인수는 다음과 같습니다.

```
date
```

`response()` 인스턴스화에 의해 설정된 요청 데이터입니다.

``` 
media_type=None
```

선택사항. 제공되는 경우 콘텐츠 협상 단계에서 결정한대로 허용되는 미디어 타입입니다.  
클라이언트의 `Accept:` 헤더에 따라 renderer의 `media_type`속성보다 더 구체적 일 수 있으며, 미디어 타입 parameter가 포함될 수 있습니다. 예를 들어 `"application/json; neated=true"`와 같습니다.

```
renderer_context=None
```
선택사항. 제공된 경우, 이는 뷰에서 제공하는 상황별 정보의 dict입니다.  
기본적으로 이 키에는 `view`, `request`, `response`, `args`, `kwargs` 와 같은 키가 포함됩니다.

### Example
다음은 `data` parameter가 포함된 response를 응답내용으로 반환하는 일반텍스트 렌더러의 예입니다.

```python
from django.utils.encoding import smart_unicode
from rest_framework import renderers


class PlainTextRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        return data.encode(self.charset)
```

### Setting the character set
기본적으로 renderer 클래스는 `UTF-8`인코딩을 사용한다고 가정합니다. 다른 인코딩을 사용하려면 renderer에서 `charset` 속성을 설정하세요.

```python
class PlainTextRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'
    charset = 'iso-8859-1'

    def render(self, data, media_type=None, renderer_context=None):
        return data.encode(self.charset)
```
renderer 클래스가 유니코드 문자열을 반환하면 인코딩을 결정하는데 사용되는 renderer의 `charset` 속성이 설정 된 `Response`클래스에 의해 응답 내용이 bytestring으로 강제 변환됩니다.  
renderer가 기존 이진 내용을 나타내는 바이트 테스트를 반환하는 경우 response의 `charset`값을 `None`으로 설정해야 합니다.(response의 `Content-Type`헤더에 `charset`값이 설정되지 않도록 보장합니다.)  
경우에 따라 `renderer_style`속성을 `binary`로 설정할 수도 있습니다. 그렇게 하면 browsable API가 이진 컨텐츠를 문자열로 표시하지 않게 됩니다.

```python
class JPEGRenderer(renderers.BaseRenderer):
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data
```

---

## Advanced renderer usage
REST 프레임워크의 renderer를 사용하여 매우 유연한 작업을 수행 할 수 있습니다. 몇가지 예...

- 요청한 미디어 타입에 따라 같은 엔드포인트에서 플랫 또는 중첩된 표현을 제공하세요.
- 일반 HTML 웹 페이지와 JSON 기반의 API응답을 동일한 엔드포인트에서 제공하세요.
- 사용할 API 클라이언트에 대해 여러 타입의 HTML 표현을 지정하세요.
- `media_type = 'image/*'`을 사용하는 것과 같이 renderer의 미디어 타입을 지정하고 `Accept`헤더를 사용하여 response의 인코딩을 변경합니다.

### Varying behaviour by media type
경우에 따라 view에서 허용되는 미디어 타입에 따라 다른 serializer 스타일을 사용하는 것이 좋습니다. 이 작업을 수행해야하는 경우 `request.accepted_renderer`에 액서스하여 response에 사용될 협상 된 renderer를 결정할 수 있습니다.

예:

```python
@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def list_users(request):
    """
    A view that can return JSON or HTML representations
    of the users in the system.
    """
    queryset = Users.objects.filter(active=True)

    if request.accepted_renderer.format == 'html':
        # TemplateHTMLRenderer takes a context dict,
        # and additionally requires a 'template_name'.
        # It does not require serialization.
        data = {'users': queryset}
        return Response(data, template_name='list_users.html')

    # JSONRenderer requires serialized data as normal.
    serializer = UserSerializer(instance=queryset)
    data = serializer.data
    return Response(data)
```

### Underspecifying the media type (미디어 타입을 지정하지 않음)
경우에 따라 renderer가 다양한 미디어타입을 제공해야 할 수도 있습니다. 이 경우 `image/*`이나 `*/*`과 같은 `media_type`값을 사용하여 미디어 타입을 명확하게 지정할 수 있습니다.  
renderer의 미디어 타입을 명시하지 않은 경우 `content_type`속성을 사용하여 response을 반환 할 때 명시적으로 미디어타입을 지정해야합니다. 예:

```python
return Response(data, content_type='image/png')
```

### Designing your media types
많은 웹 API를 위해, 하이퍼링크 관계를 갖는 단순 `JSON` 응답은 충분할 수 있다. RESTful 디자인과 [`HATEOAS`](http://timelessrepo.com/haters-gonna-hateoas)를 완전히 포용하려면 미디어타입의 디자인과 사용법을 더 자세히 고려해야합니다.

[the words of Roy Fielding](http://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven)에서는 _"REST API는 리소스를 표현하고 애플리케이션 상태를 유도하거나 기존 표준 미디어 타입에 대한 확장 관계 이름 및 `/` 또는 하이퍼 텍스트 사용 가능 마크 업을 정의하는 데 사용되는 미디어 유형을 정의하는데 필요한 모든 노력을 기울여야합니다."_  
custom 미디어 타입의 좋은 예는 GitHub의 custom [application/vnd.github+json](https://developer.github.com/v3/media/) 미디어 타입 사용과 Mike Amundsen의 IANA 승인 [application/vnd.collection+json](http://www.amundsen.com/media-types/collection/)기반 하이퍼 미디어를 참조하십시오.

### HTML error views
일반적으로, renderer는 `Http404`나 `PermissionDenied`예외 또는 `APIException`의 서브 클래스와 같이 일반 response를 처리하는지 또는 예외가 발생하여 response가 발생하는지에 관계없이 동일하게 동작합니다.  
`TemplateHTMLRenderer` 또는 `StaticHTMLRenderer`를 사용중이고 예외가 발생하면 동작이 약간 다르며 [Django's default handling of error views](https://docs.djangoproject.com/en/1.10/topics/http/views/#customizing-error-views)가 그대로 반영됩니다.  
HTML renderer에 의해 발생되고 처리되는 예외는 우선 순위에 따라 다음 방법 중 하나를 사용하여 렌더링을 시도합니다.  

- `{status_code}.html`이라는 템플릿을 로드하고 렌더링합니다.
- `api_exception.html`이라는 템플릿을 로드하고 렌더링합니다.
- HTTP 상태 코드와 텍스트를 렌더링합니다.(ex. `"404 Not Found"`)  

템플릿은 `status_code`와 `detail` 키를 포함하는 `RequestContext`로 렌더링됩니다.  

**Note**: `DEBUG=True`이면 Django의 표준 추적 오류 페이지가 HTTP 상태 코드와 텍스트를 렌더링하는 대신 표시됩니다.

---

## Third party packages
다음의 타사 패키지도 제공됩니다.

### YAML
[REST framework YAML](http://jpadilla.github.io/django-rest-framework-yaml/)은 [YAML](http://www.yaml.org/) 파싱 및 렌더링 지원을 제공합니다. 이전에 REST 프레임 워크 패키지에 직접 포함되어 있었으며 이제는 타사 패키지로 대신 지원됩니다.

#### 설치 및 구성
pip을 사용해 설치합니다.

```
$ pip install djangorestframework-yaml
```
REST 프레임워크 설정을 수정합니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_yaml.parsers.YAMLParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_yaml.renderers.YAMLRenderer',
    ),
}
```

### XML
[REST Framework XML](http://jpadilla.github.io/django-rest-framework-xml/)은 간단한 비공식 XML 형식을 제공합니다. 이전에 REST 프레임 워크 패키지에 직접 포함되어 있었으며 이제는 타사 패키지로 대신 지원됩니다.

#### 설치와 구성
pip를 사용하여 설치합니다.

```
$ pip install djangorestframework-xml
```
REST 프레임워크 설정을 수정합니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_xml.parsers.XMLParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_xml.renderers.XMLRenderer',
    ),
}
```

### JSONP
[REST framework JSONP](http://jpadilla.github.io/django-rest-framework-jsonp/)는 JSONP 렌더링을 지원합니다. 이전에 REST 프레임워크 패키지에 직접 포함되어 있었으며 이제는 타사 패키지로 대신 지원됩니다.

---
**Warning**: 도메인 간 AJAX 요청이 필요한 경우 일반적으로 `JSONP` 대신 CORS의 최신 접근 방식을 사용해야합니다. 자세한 내용은 [CORS 설명서](http://www.django-rest-framework.org/topics/ajax-csrf-cors/)를 참조하십시오.  
`jsonp` 접근법은 본질적으로 브라우저 해킹이며 `GET` 요청이 인증되지 않고 사용자 권한이 필요하지 않은 [전 세계적으로 읽을 수 있는 API 엔드포인트](http://stackoverflow.com/questions/613962/is-jsonp-safe-to-use)에만 적합합니다.

---

#### 설치와 구성
pip를 사용하여 설치합니다.

```
$ pip install djangorestframework-jsonp
```
REST 프레임워크 설정을 수정합니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_jsonp.renderers.JSONPRenderer',
    ),
}
```

### MessagePack
[MessagePack]()은 빠르고 효율적인 바이너리 serializer 형식입니다. [Juan Riaza]()는 MessagePack 렌더러와 REST 프레임 워크에 대한 파서 지원을 제공하는 [djangorestframework-msgpack 패키지]()를 유지 관리합니다.
### CSV
쉼표로 구분 된 값은 스프레드 시트 응용 프로그램으로 쉽게 가져올 수 있는 일반 텍스트 형식의 데이터 형식입니다. [Mjumbe Poe](https://github.com/mjumbewu)는 REST 프레임 워크에 대한 CSV 렌더러 지원을 제공하는 [djangorestframework-csv](https://github.com/mjumbewu/django-rest-framework-csv) 패키지를 유지 관리합니다.

### UltraJSON
[UltraJSON](https://github.com/esnme/ultrajson)은 상당히 빠른 JSON 렌더링을 제공 할 수 있는 최적화 된 C JSON 인코더입니다. [Jacob Haslehurst](https://github.com/hzy)는 UJSON 패키지를 사용하여 JSON 렌더링을 구현하는 [drf-ujson-renderer](https://github.com/gizmag/drf-ujson-renderer) 패키지를 유지 관리합니다.

### CamelCase JSON
[djangorestframework-camel-case](https://github.com/vbabiy/djangorestframework-camel-case)는 REST 프레임워크를 위한 parser와 camel-case JSON 렌더러를 제공합니다. 이를 통해 serializer는 파이썬 스타일의 underscored 필드 이름을 사용할 수 있지만, 자바 스크립트 스타일의 camel case field names으로 API에 표시됩니다. 그것은 [Vitaly Babiy](https://github.com/vbabiy)에 의해 관리됩니다.

### Pandas (CSV, Excel, PNG)
[Django REST Pandas](https://github.com/wq/django-rest-pandas)는 Pandas DataFrame API를 통해 추가 데이터 처리 및 출력을 지원하는 serializer 및 렌더러를 제공합니다. Django REST Pandas에는 판다 스타일 CSV 파일, Excel 통합 문서 (`.xls` 및 `.xlsx`) 및 [기타 다양한 형식](https://github.com/wq/django-rest-pandas#supported-formats)의 렌더러가 포함되어 있습니다. [wq 프로젝트](https://github.com/wq)의 일환으로 [S. Andrew Sheppard](https://github.com/sheppard)에 의해 유지 관리됩니다.

### LaTeX
[Rest Framework Latex는 Laulatex](https://github.com/mypebble/rest-framework-latex)를 사용하여 PDF를 출력하는 렌더러를 제공합니다. 이것은 [Pebble (S/F Software)](https://github.com/mypebble)에서 관리합니다.
