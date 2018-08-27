# Django REST Framework - Schemas

---

_"A machine-readable [schema] describes what resources are available via the API, what their URLs are, how they are represented and what operations they support."_  

_"기계 판독 가능한 [스키마]는 API를 통해 사용할 수있는 리소스, 해당 URL의 의미, 표현 방법 및 지원 작업을 설명합니다."_  

_— Heroku, JSON Schema for the Heroku Platform API_

---

## Schemas
API schema는 참조 문서를 생성하거나 API와 상호 작용 할 수 있는 동적 클라이언트 라이브러리를 구동하는 등 다양한 사용 사례를 허용하는 유용한 도구입니다.

### Representing schemas internally (내부적으로 스키마 표현하기)
REST 프레임워크는 형식 독립적인 표현으로 스키마 정보를 모델링하기 위해 [Core API](http://www.coreapi.org/)를 사용합니다. 이 정보는 다양한 스키마 형식으로 렌더링되거나 API 문서를 생성하는데 사용됩니다.  
Core API를 사용하는 경우 스키마는 API에 대한 정보의 최상위 컨테이너 객체인 문서로 표시됩니다. 사용 가능한 API 상호작용은 링크 객체를 사용하여 표시됩니다. 각 링크는 URL, HTTP 메서드를 포함하며 API 엔드포인트에서 승인 할 수 있는 매개변수를 설명하는 `Field` 인스턴스 목록을 포함할 수 있습니다. `Link`와 `Field` 인스턴스에는 API 스키마를 사용자 문서로 렌더링 할 수 있는 설명이 포함될 수도 있습니다.  
다음은 단일 검색 엔드포인트를 포함하는 API 설명의 예입니다.

```python
coreapi.Document(
    title='Flight Search API',
    url='https://api.example.org/',
    content={
        'search': coreapi.Link(
            url='/search/',
            action='get',
            fields=[
                coreapi.Field(
                    name='from',
                    required=True,
                    location='query',
                    description='City name or airport code.'
                ),
                coreapi.Field(
                    name='to',
                    required=True,
                    location='query',
                    description='City name or airport code.'
                ),
                coreapi.Field(
                    name='date',
                    required=True,
                    location='query',
                    description='Flight date in "YYYY-MM-DD" format.'
                )
            ],
            description='Return flight availability and prices.'
        )
    }
)
```

### Schema output formats
HTTP response으로 표시되려면 내부 표현이 response에 사용 된 실제 바이트로 렌더링되어야 합니다.  
[Core JSON]()은 Core API와 함께 사용하기 위한 표준 형식으로 설계되었습니다. REST 프레임워크에는 이 미디어 유형을 처리하기 위한 렌더러 클래스가 포함되어 있으며, 이 렌더러클래스는 `CoreJSONRenderer`로 사용할 수 있습니다.  
[Open API](https://openapis.org/)("Swagger"), [JSON HyperSchema](http://json-schema.org/latest/json-schema-hypermedia.html), [API Blueprint](https://apiblueprint.org/)와 같은 다른 스키마 형식도 custom renderer 클래스를 구현하여 지원할 수 있습니다.
 
### Schemas vs Hypermedia
Core API는 API 스키마에 대한 대안적인 상호작용 스타일을 제시하는 하이퍼 미디어 응답을 모델링하는데 사용될 수 있다는 점을 여기서 지적 할 필요가 있습니다.  
API 스키마를 사용할 수 있는 전체 인터페이스가 단일 엔드포인트로 제공됩니다. 개별 API 엔드포인트에 대한 응답은 일반적으로 각 response에 추가 상호 작용없이 일반 데이터로 표시됩니다.  
Hypermedia를 사용하면 클라이언트에 데이터와 사용 가능한 상호 작용이 모두 포함된 문서가 제공됩니다. 각 상호 작용을 통해 현재 상태와 사용 가능한 상호 작용을 자세히 설명하는 새 문서가 생성됩니다.  
REST 프레임워크를 사용하여 Hypermedia API를 빌드하는데 대한 자세한 정보와 지원은 향후 버전에서 계획됩니다.

---

## Adding a schema
REST 프레임워크에 대한 스키마 지원을 추가하려면 `coreapi` 패키지를 설치해야합니다.

```
pip install coreapi
```
REST 프레임워크에는 스키마 자동 생성 기능이 포함되어 있거나 명시적을 스키마를 지정할 수 있습니다. 필요한 항목에 따라 API에 스키마를 추가하는 몇가지 방법이 있습니다.

### The get_schema_view shortcut
프로젝트에 스키마를 포함시키는 가장 간단한 방법은 `get_schema_view()`함수를 사용하는 것입니다.

```python
schema_view = get_schema_view(title="Server Monitoring API")

urlpatterns = [
    url('^$', schema_view),
    ...
]
```
view가 추가되면 자동 생성 스키마 정의를 검색하기 위한 API 요청을 할 수 있습니다.

```python
$ http http://127.0.0.1:8000/ Accept:application/vnd.coreapi+json
HTTP/1.0 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/vnd.coreapi+json

{
    "_meta": {
        "title": "Server Monitoring API"
    },
    "_type": "document",
    ...
}
```
`get_schema_view()`에 대한 인수는 다음과 같습니다.

- `title` : 스키마 정의를 설명하는 제목을 제공하는데 사용할 수 있습니다.
- `url` : 스키마의 표준 URL을 전달하는데 사용될 수 있습니다.

```python
schema_view = get_schema_view(
    title='Server Monitoring API',
    url='https://www.example.org/api/'
)
```

- `urlconf` : API 스키마를 생성하려는 URL conf의 가져오기 경로를 나타내는 문자열입니다. 기본값은 Django의 `ROOT_URLCONF` 설정 값입니다.

```python
schema_view = get_schema_view(
    title='Server Monitoring API',
    url='https://www.example.org/api/',
    urlconf='myproject.urls'
)
```

- `renderer_classes` : API root 엔드포인트의 렌더링에 사용할 수 있는 렌더러 클래스 셋을 전달하는데 사용할 수 있습니다.  

```python
from rest_framework.renderers import CoreJSONRenderer
from my_custom_package import APIBlueprintRenderer

schema_view = get_schema_view(
    title='Server Monitoring API',
    url='https://www.example.org/api/',
    renderer_classes=[CoreJSONRenderer, APIBlueprintRenderer]
)
```

### Using an explicit schema view
`get_schema_view()` shortcut이 제공하는 것보다 더 많은 컨트롤이 필요한 경우 `SchemaGenerator` 클래스를 직접 사용하여 Document 인스턴스를 자동으로 생성하고 뷰에서 이를 반환 할 수 있습니다.  
이 옵셥을 사용하면 원하는 모든 동작으로 스키마 엔드포인트를 설정할 수 있습니다. 예를 들어, 스키마 엔드포인트에 다른 사용 권한, 제한 또는 인증 정책을 적용 할 수 있습니다.  
다음은 `SchemaGenerator`를 뷰와 함께 사용하려 스키마를 반환하는 예제입니다.

get_schema_view () 바로 가기가 제공하는 것보다 더 많은 컨트롤이 필요한 경우 SchemaGenerator 클래스를 직접 사용하여 Document 인스턴스를 자동으로 생성하고 뷰에서이를 반환 할 수 있습니다.

**views.py**:

```python
from rest_framework.decorators import api_view, renderer_classes
from rest_framework import renderers, response, schemas

generator = schemas.SchemaGenerator(title='Bookings API')

@api_view()
@renderer_classes([renderers.CoreJSONRenderer])
def schema_view(request):
    schema = generator.get_schema(request)
    return response.Response(schema)
```

**urls.py**:

```python
urlpatterns = [
    url('/', schema_view),
    ...
]
```
사용 가능한 권한에 따라 다른 사용자에게 다른 스키마를 제공할 수도 있습니다. 이 접근법은 인증되지 않은 요청이 인증된 요청과 다른 스키마로 제공되거나 API의 다른 부분이 해당 역할에 따라 다른 사용자에게 표시되도록하는데 사용할 수 있습니다.  
사용자 권한으로 필터링 된 엔드포인트가 있는 스키마를 표시하려면 `get_schema()`메서드에 `request` 인수를 전달해야 합니다. 예를 들면 다음과 같습니다.

```python
@api_view()
@renderer_classes([renderers.CoreJSONRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Bookings API')
    return response.Response(generator.get_schema(request=request))
```

### Explicit schema definition
자동 생성 방식의 대안은 코드베이스에 `Document` 객체를 선언하여 API 스키마를 명시적으로 지정하는 것입니다. 그렇게 하는것은 조금 더 작업 할 수 있지만 스키마 표현을 완전히 제어 할 수 있습니다.

```python
import coreapi
from rest_framework.decorators import api_view, renderer_classes
from rest_framework import renderers, response

schema = coreapi.Document(
    title='Bookings API',
    content={
        ...
    }
)

@api_view()
@renderer_classes([renderers.CoreJSONRenderer])
def schema_view(request):
    return response.Response(schema)
```

### Static schema file
마지막 옵션은 Core JSON 또는 Open API 와 같은 사용 가능한 형식 중 하나를 사용하여 API schema를 static 파일로 작성하는 것입니다.  

다음 중 하나를 수행 할 수 있습니다.

- 스키마 정의를 static 파일로 작성하고 [static 파일을 직접 제공하세요](https://docs.djangoproject.com/en/1.10/howto/static-files/).
- Core API를 사용하여 로드 된 스키마 정의를 작성한 다음 클라이언트 요청에 따라 여러가지 사용 가능한 형식중 하나로 렌더링합니다.

---

## Schemas as documentation
API 스키마의 일반적인 사용법 중 하나는 문서 페이지를 작성하는데 사용합니다.  
REST 프레임워크의 스키마 생성은 docstring을 사용하여 스키마 문서의 설명을 자동으로 채웁니다.  

이 설명은 다음을 기반으로 합니다.  

- 해당 메소드 docstring이 있는 경우는 그것을 돌려줍니다.
- docstring 클래스 내의 명명된 섹션으로, 한 줄 또는 여러 줄이 될 수 있습니다.
- The class docstring.

### Examples
명시적인 메서드 docstring이 있는 `APIView`입니다.

```python
class ListUsernames(APIView):
    def get(self, request):
        """
        Return a list of all user names in the system.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)
```
설명하는 액션 docstring이 있는 `ViewSet`입니다.

```python
class ListUsernames(ViewSet):
    def list(self, request):
        """
        Return a list of all user names in the system.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)
```
단일 행 스타일을 사용하여 docstring 클래스의 섹션이 있는 generic view입니다.

```python
class UserList(generics.ListCreateAPIView):
    """
    get: List all the users.
    post: Create a new user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
```
다중 회선 스타일을 사용하여 docstring 클래스의 섹션이 있는 generic viewset입니다.

```python
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.

    retrieve:
    Return a user instance.

    list:
    Return all users, ordered by most recently joined.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
```

---

## Alternate schema formats
대체 스키마 형식을 지원하려면 `Document` 인스턴스를 바이트 표현으로 변환하는 처리를 담당하는 custom의 rederer 클래스를 구현해야합니다.  
사용할 형식을 인코딩을 지원하는 Core API 코덱패키지가 있는 경우 해당 코덱을 사용하여 rederer 클래스를 구현 할 수 있습니다.

### Example
예를 들어 `openapi_codec` 패키지는 Open API("Swagger") 형식의 인코딩 또는 디코딩을 지원합니다.

```python
from rest_framework import renderers
from openapi_codec import OpenAPICodec

class SwaggerRenderer(renderers.BaseRenderer):
    media_type = 'application/openapi+json'
    format = 'swagger'

    def render(self, data, media_type=None, renderer_context=None):
        codec = OpenAPICodec()
        return codec.dump(data)
```

---

## API Reference

### SchemaGenerator
스키마를 생성하는데 사용 할 수 있는 API view를 검토하는 클래스입니다.  
일반적으로 다음과 같이 단일 인수로 `SchemaGenerator`를 인스턴스화합니다.

```
generator = SchemaGenerator(title='Stock Prices API')
```

Arguments:  

- `title` **required** : API의 이름.
- `url` : API 스키마의 루트 URL입니다. 스키마가 경로 접두어에 포함되지 않으면 이 옵션이 필요하지 않습니다.
- `patterns` : 스키마를 생성 할 때 검사 할 URL 목록입니다. 기본값은 프로젝트의 URL conf입니다.
- `urlconf` : 스키마를 생성 할 때 사용할 URL conf 모듈 이름입니다. 기본값은 `settings.ROOT_URLCONF`입니다.

#### get_schema(self, request)
API 스키마를 나타내는 `coreapi.Document` 인스턴스를 반환합니다.

```python
@api_view
@renderer_classes([renderers.CoreJSONRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Bookings API')
    return Response(generator.get_schema())
```
`request` 인수는 선택 사항이며, 결과 스키마 생성에 사용자 별 권한을 적용하려는 경우에 사용할 수 있습니다.

#### get_links(self, request)
API 스키마에 포함되어야 하는 모든 링크가 포함된 중첩된 dict를 반환합니다.  
다른 레이아웃으로 새 dict를 빌드할 수 있으므로 생성된 스키마의 결과 구조를 수정하려는 경우 이를 대체하는 것이 좋습니다.  

#### get_link(self, path, method, view)
주어진 뷰에 해당하는 `coreapi.Link`인스턴스를 반환합니다.  
특정 뷰에 대해 custom 동작을 제공해야하는 경우 이 설정을 오버라이드 할 수 있습니다.

#### get_description(self, path, method, view)
링크 설명으로 사용할 문자열을 반환합니다. 기본적으로 이는 위의 "Schemas as Documentation" 섹션에서 설명한대로 docstring을 기반으로합니다.

#### get_encoding(self, path, method, view)
지정된 뷰와 상호 작용할 때 모든  request 본문에 대한 인코딩을 나타내는 문자열을 반환합니다.  
예: `application/json`. request 본문을 기대하지 않는 뷰에 빈 문자열을 반환할 수 있습니다.

#### get_path_fields(self, path, method, view):
`coreapi.Link()`인스턴스의 list를 반환합니다. URL의 각 경로 parameter에 하나씩.

#### get_serializer_fields(self, path, method, view)
`coreapi.Link()` 인스턴스의 list를 반환합니다. 뷰가 사용하는 serializer 클래스의 각 필드에 하나씩.

#### get_pagination_fields(self, path, method, view)
뷰가 사용하는 pagination 클래스의 `get_schema_fields()` 메소드가 반환 한 `coreapi.Link()` 인스턴스의 list를 반환합니다.

#### get_filter_fields(self, path, method, view)
뷰에 의해 사용 된 filter 클래스의 `get_schema_fields()` 메소드에 의해 돌려 주어지는 `coreapi.Link()` 인스턴스의  list를 돌려줍니다.

---

### Core API

이 문서는 API 스키마를 표현하는데 사용되는 `coreapi` 패키지 내의 구성 요소에 대한 간략한 개요를 제공합니다.  
이러한 클래스는 `rest_framework` 패키지가 아니라 `coreapi`패키지에서 가져옵니다.  

#### Document
API 스키마 컨테이너를 나타냅니다.  
`title` : API의 이름  
`url` : API의 표준 URL  
`content` : 스키마에 포함 된 `Link` 개체를 포함하는 dict입니다.  

스키마에 더 많은 구조를 제공하기 위해 content dict는 일반적으로 두번째 레벨로 중첩 될 수 있습니다.  
예:

```python
content={
    "bookings": {
        "list": Link(...),
        "create": Link(...),
        ...
    },
    "venues": {
        "list": Link(...),
        ...
    },
    ...
}
```

#### Link
개별 API 엔드포인트를 나타냅니다.

`url` : 엔드포인트의 URL. `/users/{username}/`와 같은 URI 템플릿 일 수 있습니다.  
`action` : 엔드포인트와 연관된 HTTP 방법. 하나 개 이상의 HTTP 메서드를 지원하는 URL은, 각각 하나의 `Link`에 해당해야합니다.  
`fields` : 입력에 사용 할 수 있는 parameter를 설명하는 `Field`인스턴스의 list입니다.  
`description` : 엔드포인트의 의미와 용도에 대해 간단한 설명.

#### Field
지정된 API 엔드포인트에서 단일 입력 매개변수를 나타냅니다.  

`name` : 입력을 설명하는 이름입니다.  
`required` : 클라이언트가 값을 포함하는 경우 또는 parameter를 생략할 수 있는지 여부를 나타내는 boolean 입니다.  
`location` : 정보가 request에 어떻게 인코딩되는지 결정합니다. 다음 문자열 중 하나이어야 합니다.  
>
**"path"**  
템플릿 화 된 URL에 포함됩니다. 예를 들어 `/products/slim-fit-jeans/`와 같은 URL path에서 API 입력을 처리하기 위해 `/products/{product_code}/`의 URL 값을 `"path"` 입력란과 함께 사용할 수 있습니다.  
이 필드는 대개 [프로젝트 URL conf의 명명 된 인수](https://docs.djangoproject.com/en/1.10/topics/http/urls/#named-groups)와 일치합니다.  
>
**"query"**  
URL 쿼리 매개변수로 포함됩니다. 예: `?search=sale`. 일반적으로 `GET` 요청에 사용됩니다.  
이러한 필드는 일반적으로 뷰의 pagination 및 필터링 컨트롤과 일치합니다.  
>
**"form"**
request 본문에 JSON 객체 또는 HTML 양식의 단일 항목으로 포함됩니다. 예 : `{"color":"blue",...}`. 일반적으로 `POST`, `PUT` 및 `PATCH` 요청에 사용됩니다. 여러 `"form"`입력란은 단일 링크에 포함될 수 있습니다.  
이러한 필드는 일반적으로 뷰의 serializer 필드와 일치합니다.
>
**"body"**
전체 request 본문에 포함됩니다. 일반적으로 `POST`, `PUT`및 `PATCH` 요청에 사용됩니다. 링크에는 둘 이상의 `"body"` 필드가 존재 할 수 없습니다. `"form"`필드와 함께 사용 할 수 없습니다.  
이러한 필드는 보통 `ListSerializer`를 사용하는 request 입력의 유효성을 검사하거나 파일 업로드 뷰를 사용하는 view와 일치합니다.

`encoding`  
>
**"application/json"**  
JSON 인코딩 된 request 컨텐츠. `JSONParser`를 사용하는 뷰에 해당합니다. 하나 이상의 `location="form"`필드 또는 단일 `location="body"`필드가 링크에 포함 된 경우에만 유효합니다.  
>
**"multipart/form-data"**  
멀티 파트로 인코딩 된 request content. `MultiPartParser`를 사용하는 뷰에 해당합니다 하나 이상의 `location="form"`필드가 링크에 포함 된 경우에만 유효합니다.  
>
**"application/x-www-form-urlencoded"**  
URL로 인코딩 된 requetst content. `FormParser`를 사용하는 뷰에 해당합니다. 하나 이상의 `location="form"`필드가 링크에 포함 된 경우에만 유효합니다.  
>
**"application/octet-stream"**  
이진 업로드 request content. `FileUploadParser`를 사용하는 뷰에 해당합니다. `location="body"`필드가 링크에 포함된 경우에만 유효합니다.

`description` : 입력 필드의 의미와 용도에 대한 간단한 설명
