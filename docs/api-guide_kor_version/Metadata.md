# Django REST Framework - Metadata

---

_"[The OPTIONS] method allows a client to determine the options and/or requirements associated with a resource, or the capabilities of a server, without implying a resource action or initiating a resource retrieval."_  
  
_"[OPTIONS] 메소드는 클라이언트가 자원 동작을 암시하거나 자원 검색을 시작하지 않고 자원 또는 서버의 기능과 관련된 옵션 및 `/` 또는 요구 사항을 결정할 수 있게 합니다."_  

_— RFC7231, Section 4.3.7._

---

## Metadata
REST 프레임워크는 API가 `OPTIONS` 요청에 어떻게 응답해야 하는지를 결정하기 위한 구성 가능한 메커니즘을 포함합니다. API 스키마 또는 기타 리소스 정보를 반환 할 수 있습니다.  
현재 HTTP OPTIONS 요청에 대해 어떤 스타일의 response를 반환해야하는지에 대해 널리 채택 된 규칙이 없으므로 유용한 정보를 반환하는 특별 스타일을 제공합니다.  
다음은 기본적으로 반환되는 정보를 보여주는 예제 response입니다.

```python
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json

{
    "name": "To Do List",
    "description": "List existing 'To Do' items, or create a new item.",
    "renders": [
        "application/json",
        "text/html"
    ],
    "parses": [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data"
    ],
    "actions": {
        "POST": {
            "note": {
                "type": "string",
                "required": false,
                "read_only": false,
                "label": "title",
                "max_length": 100
            }
        }
    }
}
```

### Setting the metadata scheme
`DEFAULT_METADATA_CLASS`설정 키를 사용하여 메타 데이터 클래스를 전역으로 설정할 수 있습니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata'
}
```
또는 view에 대해 개별적으로 메타 데이터 클래스를 설정할 수 있습니다.

```python
class APIRoot(APIView):
    metadata_class = APIRootMetadata

    def get(self, request, format=None):
        return Response({
            ...
        })
```
REST 프레임워크 패키지는 `SimpleMetadata`라는 단일 메타 데이터 클래스 구현만 포함됩니다. 다른 스타일을 사용하려면 custom 메타 데이터 클래스를 구현해야합니다.

### Creating schema endpoints
일반 `GET` 요청으로 액서스되는 schema endpoint을 만들기 위한 특정 요구사항이 있는 경우 그렇게 하기 위해 메타 데이터 API를 다시 사용할 수 있습니다.  
예를 들어, 다음과 같은 추가 라우트를 vViewSet에 사용하여 linkable schema endpoint에 제공할 수  있습니다.

```python
@list_route(methods=['GET'])
def schema(self, request):
    meta = self.metadata_class()
    data = meta.determine_metadata(request, self)
    return Response(data)
```
`OPTIONS` 응답을 [캐싱할 수 없다는 것](https://www.mnot.net/blog/2012/10/29/NO_OPTIONS)을 포함하여 이 접근 방식을 선택할 수 있는 몇가지 이유가 있습니다.

---

## Custom metadata classes
custom metadata 클래스를 제공하려면 `BaseMetadata`를 대체하고 `decide_metadata(self, request, view)` 메서드를 구현해야합니다.  
유용한 정보로는 schema 정보 리턴, [JSON schema](http://json-schema.org/)와 같은 형식 사용 또는 관리자에세 디버그 정보 리턴 등이 있습니다.

### Example
다음 클래스는 `OPTIONS` 요청에 반환되는 정보를 제한하는데 사용될 수 있습니다.

```python
class MinimalMetadata(BaseMetadata):
    """
    Don't include field and other information for `OPTIONS` requests.
    Just return the name and description.
    """
    def determine_metadata(self, request, view):
        return {
            'name': view.get_view_name(),
            'description': view.get_view_description()
        }
```
그런 다음 이 custom 클래스를 사용하도록 설정을 구성하세요.

```python
REST_FRAMEWORK = {
    'DEFAULT_METADATA_CLASS': 'myproject.apps.core.MinimalMetadata'
}
```

## Third party packages
다음의 타사 패키지는 추가 메나 데이터 구현을 제공합니다.

### DRF-schema-adapter
[drf-schema-adapter]()는 프론트엔드 프레임워크 및 라이브러리에 스키마 정보를 보다 쉽게 제공할 수 있게 해주는 도구 set입니다.  metadata mixin 뿐만 아니라 다양한 라이브러리에 의해 읽을 수 있는 스키마 정보뿐만 아니라 [json-schema](http://json-schema.org/)를 생성하는데 적합한 2개의 metadara 클래스와 여러 어댑터를 제공합니다.  
특정 프론트엔드에서 작동하도록 어댑터를 작성할 수도 있습니다. 그렇게 하고 싶다면 스키마 정보를 json 파일로 내보낼 수 있는 내보내기 기능을 제공합니다.
