# Django REST Framework -  Parsers

---

_"Machine interacting web services tend to use more structured formats for sending data than form-encoded, since they're sending more complex data than simple forms"_  

_"웹 서비스를 상호 작용하는 기계는 단순한 형식보다 복잡한 데이터를 전송하기 때문에 양식으로 인코딩 된 것보다 데이터 전송에 더 많은 구조화 된 형식을 사용하는 경향이 있습니다."_  

_— Malcom Tredinnick, Django developers group_

---

## Parsers
REST 프레임워크에는 `Parser`클래스가 내장되어 있어 다양한 미디어 타입으로 requests를 수락할 수 있습니다. 또한 `custom parser`를 정의 할 수 있어서 API에서 허용하는 미디어 타입을 유연하게 디자인 할 수 있습니다.

### How the parser is determined
뷰에 대한 유효한 parser set은 항상 클래스 목록으로 정의됩니다. `request.data`에 액서스하면 REST 프레임워크는 들어오는 request의 `Content-Type` 헤더를 검사하고 request 내용을 parse하는데 사용할 `parser`를 결정합니다.

---
**Note**: 클라이언트 응용 프로그램을 개발할 때는 항상 HTTP request로 데이터를 보낼때 `Content-Type`헤더를 설정해야 합니다.  
콘텐트 타입을 설정하지 않으면 대부분의 클라이언트는 `'application/x-www-form-urlencoded'`를 기본값으로 사용합니다. 이는 원하지 않을 수 있습니다.  
예를 들어, `.ajax()`메서드로 jQuery를 사용하여 `json`으로 인코딩 된 데이터를 보내는 경우, `contentType: 'application/json'`설정을 포함해야 합니다.

---

### Setting the parsers
`parser`의 기본 set은 `DEFAULT_PARSER_CLASSES`  설정을 사용하여 전역으로 설정할 수 있습니다. 예를 들어, 다음 설정은 기본 JSON 이나 formdata 대신 JSON 컨텐트가 있는 requests만 허용합니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    )
}
```
`APIView`클래스의 기본 views를 사용하여 개별 view나 viewset에 사용되는 `parser`를 설정할 수도 있습니다.

```python
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

class ExampleView(APIView):
    """
    A view that can accept POST requests with JSON content.
    """
    parser_classes = (JSONParser,)

    def post(self, request, format=None):
        return Response({'received data': request.data})
```
또는 FBV와 함께 `@api_view`데코레이터를 사용하는 경우.

```python
from rest_framework.decorators import api_view
from rest_framework.decorators import parser_classes

@api_view(['POST'])
@parser_classes((JSONParser,))
def example_view(request, format=None):
    """
    A view that can accept POST requests with JSON content.
    """
    return Response({'received data': request.data})
```

---

## API Reference

### JSONParser
`JSON` request content를 파싱합니다.  
**.media_type**: `application/json`

### FormParser
HTMl form content를 파싱합니다. `request.data`는 데이터의 `QueryDict`로 채워집니다.  
일반적으로 HTML form data를 완벽하게 지원하기 위해 `FormParser`와 `MultiPartParser`를 함께 사용하려고 합니다.  
**.media_type**: `application/x-www-form-urlencoded`

### MultiPartParser
파일 업로드를 지원하는 `Multi form content`를 파싱합니다. 두 `request.data` 모두 `QueryDict`로 채워집니다.  
일반적으로 HTML form data를 완벽하게 지원하기 위해 `FormParser`와 `MultiPartParser`를 함께 사용하려고 합니다.  
**.media_type**: `multipart/form-data`

### FileUploadParser
가공되지 않은 file upload content를 파싱함니다. `request.data` 속성은 업로드 된 파일을 포함하는 단일 키`'file'`이 포함된 dict입니다.  
`FileUploadParser`와 함께 사용 된 view가 파일 이름 URL 키워드 인수로 호출되면 해당 인수가  filename 으로 사용됩니다.  
`filename` URL 키워드 인수없이 호출되면 클라이언트는 `Content-Disposition` HTTP 헤더에 filename을 설정해야 합니다. 예를 들면, `Content-disposition: attachment; filename=upload.jpg`  
**.media_type**: `*/*`

###### notes:

- `FileUploadParser`는 파일을 가공되지 않은 데이터 request으로 업로드 할 수 있는 기본 클라이언트에서 사용하기 위한 것입니다. 웹 기반 업로드 또는 멀티 파트 업로드가 지원되는 기본 클라이언트의 경우 `MultiPartParser` 파서를 대신 사용해야합니다.
- 이 파서의 `media_type`은 모든 콘텐트 타입과 일치하므로 `FileuploadParser`는 일반적으로 API view에 설정된 유일한 `parser` 이어야 합니다.
- `FileUploadParser`는 Django의 표준 `FILE_UPLOAD_HANDLERS` 설정과 `request.upload_handlers` 속성을 고려합니다. 자세한 내용은 [Django 문서](https://docs.djangoproject.com/en/1.10/topics/http/file-uploads/#upload-handlers)를 참조하세요.

###### Basic usage example:

```python
# views.py
class FileUploadView(views.APIView):
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        file_obj = request.data['file']
        # ...
        # do some stuff with uploaded file
        # ...
        return Response(status=204)

# urls.py
urlpatterns = [
    # ...
    url(r'^upload/(?P<filename>[^/]+)$', FileUploadView.as_view())
]
```
---

## Custom parsers
`custom parser`를 구현하려면 `BaseParser`를 오버라이드하고 `.media_type`속성을 설정하고 `.parse(self, stream, media_type, parser_context)`메소드를 구현해야 합니다.  
메서드는 `request.data`속성을 채우는데 사용할 데이터를 반환해야합니다.  
`.parse()`에 전달된 인수는 다음과 같습니다.   

### stream
request의 본문을 나타내는 스트림과 같은 객체입니다.

### media_type
선택사항. 제공되는 경우 들어오는 request content의 미디어 타입입니다.  
request의 `Content-Type:` 헤더에 따라 렌더러의 `media_type`속성보다 더 구체적일 수 있으며, 미디어 타입 parameter가 포함 될 수 있습니다. 예: `"text/plain; charset=utf-8"`

### parser_context
선택사항. 이 인수가 제공되면 request content을 파싱하는데 필요할 수 있는 추가 context를 포함하는 dict가 됩니다.  
기본적으로 `view`, `request`, `args`, `kwargs` 키들이 포함됩니다.

### Example
다음은 request content를 나타내는 문자열로 `request.data`속성을 채우는 일반 텍스트 파서의 예입니다.

```python
class PlainTextParser(BaseParser):
    """
    Plain text parser.
    """
    media_type = 'text/plain'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Simply return a string representing the body of the request.
        """
        return stream.read()
```

---

## Third party packages
다음의 타사 패키지도 제공됩니다.

### YAML
[REST 프레임 워크 YAML](http://jpadilla.github.io/django-rest-framework-yaml/)은 [YAML](http://www.yaml.org/) 파싱 및 렌더링 지원을 제공합니다. 이전에 REST 프레임워크 패키지에 직접 포함되어 있었으며 이제는 타사 패키지로 대신 지원됩니다.

###### 설치 및 구성 
pip를 사용하여 설치합니다.

```
$ pip install djangorestframework-yaml
```
REST 프레임워크 설정을 수정하세요.

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

[REST 프레임워크 XML](http://jpadilla.github.io/django-rest-framework-xml/)은 간단한 비공식 XML 형식을 제공합니다. 이전에 REST 프레임 워크 패키지에 직접 포함되어 있었으며 이제는 타사 패키지로 대신 지원됩니다.

###### 설치 및 구성
pip를 사용하여 설치합니다.

```
$ pip install djangorestframework-xml
```
REST 프레임워크 설정을 수정하세요.

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

### MessagePack
[MessagePack](https://github.com/juanriaza/django-rest-framework-msgpack)은 빠르고 효율적인 바이너리 serializer 형식입니다. [Juan Riaza](https://github.com/juanriaza)는 MessagePack 렌더러와 REST 프레임 워크에 대한 파서 지원을 제공하는 [djangorestframework-msgpack 패키지](https://github.com/juanriaza/django-rest-framework-msgpack)를 유지 관리합니다.

### CamelCase JSON
[djangorestframework-camel-case](https://github.com/vbabiy/djangorestframework-camel-case)는 REST 프레임워크를 위한 `parser`와 camel-case JSON 렌더러를 제공합니다. 이를 통해 serializer는 파이썬 스타일의 underscored 필드 이름을 사용할 수 있지만, 자바 스크립트 스타일의 camel case field names으로 API에 표시됩니다. 그것은 [Vitaly Babiy](https://github.com/vbabiy)에 의해 관리됩니다.
