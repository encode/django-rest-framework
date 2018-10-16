# Django REST Framework - Settings

---

_"Namespaces are one honking great idea - let's do more of those!"_  

_"네임 스페이스는 훌륭한 아이디어를 제공합니다. let's do more of those!"_  
 
_— The Zen of Python_

---

## Settings
REST 프레임워크의 모든 설정은 `REST_FRAMEWORK`라는 단일 Django 설정에 네임 스페이스를 설정합니다.  
예를 들어 프로젝트의 `settings.py`파일에는 다음과 같은 내용이 포함될 수 있습니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    )
}
```

### Accessing settings
프로젝트에서 REST 프레임워크의 API 설정값에 액서스해야하는 경우 `api_settings`객체를 사용해야합니다. 예를 들면.

```python
from rest_framework.settings import api_settings

print api_settings.DEFAULT_AUTHENTICATION_CLASSES
```
`api_settings`객체는 사용자가 정의한 설정을 확인하고 그렇지 않으면 기본값을 fall back합니다. 클래스를 참조하기 위해 string import path를 사용하여 모든 설정은 문자열 리터럴 대신 참조 된 클래스를 자동으로 가져오고 반환합니다.

---

## API Reference

### API policy settings
다음 설정은 기본 API 정책을 제어하며 모든 `APIView` CBV 또는 `@api_view` FBV에 적용됩니다.

#### `DEFAULT_RENDERER_CLASSES`
`Response` 객체를 반환할 때 사용할 수 있는 renderer의 기본 set을 결정하는 rederer 클래스의 list 또는 tuple입니다.  

Default:

```python
(
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)
```
#### `DEFAULT_PARSER_CLASSES`
`request.data`속성에 액서스 할 때 사용되는 parser의 기본 set을 결정하는 parser 클래스의 list 또는 tuple입니다.

Default:

```python
(
    'rest_framework.parsers.JSONParser',
    'rest_framework.parsers.FormParser',
    'rest_framework.parsers.MultiPartParser'
)
```

#### `DEFAULT_AUTHENTICATION_CLASSES`
`request.user` 또는 `request.auth`등록 정보에 액서스할 때 사용되는 인증자의 기본 set을 판별하는 authentication 클래스의 list 또는 tuple입니다.  

Default:

```python
(
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.BasicAuthentication'
)
```

#### `DEFAULT_PERMISSION_CLASSES`
view의 시작에 체크 된 권한의 기본 set을 결정하는 permission 클래스의 list 또는 tuple입니다. permission은 list의 모든 클래스에서 부여해야합니 다.  

Default:

```python
(
    'rest_framework.permissions.AllowAny',
)
```

#### `DEFAULT_THROTTLE_CLASSES`
view의 시작에서 점검되는 기본 throttle set을 결정하는 throttle 클래스의 list 또는 tuple입니다.  

Default: `()`

#### `DEFAULT_CONTENT_NEGOTIATION_CLASS`
들어오는 request에 따라 rederer가 response에 대해 선택되는 방법을 결정하는 content negotiation 클래스 입니다.  

Default: `'rest_framework.negotiation.DefaultContentNegotiation'`

---

### Generic view settings
다음 설정은 generic CBV의 동작을 제어합니다.  

#### `DEFAULT_PAGINATION_SERIALIZER_CLASS`

---

**이 설정은 제거되었습니다.**  

pagination API는 출력 형식을 결정하기 위해 serializer를 사용하지 않으므로 대신 출력 형식 제어 방법을 지정하기 위해 pagination 클래스의 `'get_paginated_response`` 메서드를 대체해야합니다.

---

#### `DEFAULT_FILTER_BACKENDS`
generic 필터링에 사용해야 하는 filter backend 클래스 list입니다. `None`으로 설정하면 generic 필터링이 비활성화됩니다.

#### `PAGINATE_BY`

---

**이 설정은 제거 되었습니다.**  

pagination 스타일 설정에 대한 자세한 지침은 [setting the pagination style](http://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style)를 참조하세요.

---
#### `PAGE_SIZE`
pagination에 사용할 기본 페이지 크기입니다. `None`으로 설정하면 기본적으로 pagination이 비활성화됩니다.  

Default: `None`  

#### `PAGINATE_BY_PARAM`

---
**이 설정은 제거 되었습니다.**  

pagination 스타일 설정에 대한 자세한 지침은 [setting the pagination style](http://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style)를 참조하세요.

---
#### `MAX_PAGINATE_BY`

---
**이 설정은 지원 중단 예정입니다.**  

pagination 스타일 설정에 대한 자세한 지침은 [setting the pagination style](http://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style)를 참조하세요.

---
#### SEARCH_PARAM
`SearchFilter`가 사용하는 검색어를 지정하는데 사용 할 수 있는 검색어 parameter의 이름입니다.  

Default: `search`  

#### ORDERING_PARAM
`OrderingFilter`에 의해 반환 된 결과의 순서를 지정하는데 사용할 수 있는 쿼리 parameter의 이름입니다.  

Default: `ordering`

---

### Versioning settings

#### DEFAULT_VERSION
버전 정보가 없는 경우 `request.version`에 사용해야 하는 값입니다.  

Default: `None`

#### ALLOWED_VERSIONS
이 값을 설정하면 버전 체계에 의해 반환 될 수 있는 버전 set이 제한되며, 제공된 버전이 이 set에 포함되어 있지 않으면 오류가 발생합니다.  

Default: `none`  

#### VERSION_PARAM
미디어 타입 또는 URL 쿼리 parameter와 같이 모든 버젼 지정 parameter에 사용해야하는 문자열입니다.  

Default: `version`

---

### Authentication settings
다음 설정은 인증되지 않은 요청의 동작을 제어합니다.  

#### UNAUTHENTICATED_USER
인증되지 않은 요청에 대해 `request.user`를 초기화하는데 사용해야하는 클래스입니다.  

Default: `django.contrib.auth.models.AnonymousUser`  

#### UNAUTHENTICATED_TOKEN
인증되지 않은 요청에 대해 `request.auth`를 초기화하는데 사용해야 하는 클래스입니다.  

default: `None`

--

### Test settings
다음 설정은 APIRequestFactory 및 APIClient의 동작을 제어합니다.  

#### `TEST_REQUEST_DEFAULT_FORMAT`
테스트 요청을 할때 사용해야하는 기본 형식입니다.  
이 값은 `TEST_REQUEST_RENDERER_CLASSES`설정의 renderer 클래스 중 하나의 형식과 일치해야합니다.  

Default: `'multipart'`

#### `TEST_REQUEST_RENDERER_CLASSES`
테스트 요청을 작성할 때 지원되는 renderer 클래스입니다.  
`client.post('/users', {'username': 'jamie'}, format='json')` 이러한 renderer 클래스의 형식은 테스트 요청을 구성 할 때 사용할 수 있습니다.  

Default:

```python
(
    'rest_framework.renderers.MultiPartRenderer',
    'rest_framework.renderers.JSONRenderer'
)
```

---

### Schema generation controls

#### `SCHEMA_COERCE_PATH_PK`
이것을 설정하면 schema path parameter를 생성할 때 URL conf의 `'pk'`식별자를 실제 필드 이름으로 매핑합니다. 일반적으로 `'id'`가 됩니다. 이것은 "indentifer"가 좀 더 일반적인 개념인 반면 "primary key"는 세부 사항이므로 보다 적합한 표현을 제공합니다.

Default: `True`  

#### `SCHEMA_COERCE_METHOD_NAMES`
이것이 설정되면 내부 viewset 메소드 이름을 schema generation에 사용 딘 외부 액션 이름에 매핑하는데 사용됩니다. 이것은 코드 베이스에서 내부적으로 사용되는 것보다 외부 표현에 더 적합한 이름을 생성할 수 있게 해줍니다.  

Default: `{'retrieve': 'read', 'destroy': 'delete'}`

---

### Content type controls

#### `URL_FORMAT_OVERRIDE`
기본 content negotiation `Accept`을 오버라이드하는데 사용할 수 있는 URL parameter의 이름 요청 URL에서 `format=...` 쿼리 parameter를 사용하여 헤더의 동작을 허용합니다.  

예: `http://example.com/organizations/?format=csv`  

이 설정 값이 `None`이면 URL 형식 오버라이드가 비활성화 됩니다.  

Default: `'format'`  

#### `FORMAT_SUFFIX_KWARG`
format suffix를 제공하는데 사용할 수 있는 URL conf의 parameter 이름입니다. 이 설정은 format_suffix_pattern`을 사용하여 접미사로 된 URL패턴을 포함할 때 적용됩니다.  

예: `http://example.com/organizations.csv/`  

Default: `'format'`

---

### Date and time formatting
다음 설정은 날짜 및 시간 표현을 파싱하고 렌더링하는 방법을 제어하는데 사용됩니다.  

#### `DATETIME_FORMAT`
`DateTimeField` Serializer 필드의 출력을 렌더링하기 위해 기본적으로 사용해야 하는 형식 문자열입니다. `None`이면 `DateTimeField` serializer 필드는 Python `datetime`객체를 반환하고, datetime 인코딩은 렌더러에 의해 결정됩니다.  

`None`, `'iso-8601'`또는 Python [strftime format](https://docs.python.org/3/library/time.html#time.strftime) 형식 문자열 주 하나 일 수 있습니다.  

Default: `'iso-8601'`

#### `DATETIME_INPUT_FORMATS`
`DateTimeField` serializer 필드에 대한 입력을 파싱하기위해 기본적으로 사용해야하는 형식문자열 list입니다.  
문자열 `'iso-8601'`또는 python [strftime format](https://docs.python.org/3/library/time.html#time.strftime)형식 문자열을 포함하는 list일 수 있습니다.  

Default: `['iso-8601']`

#### `DATE_FORMAT`
`DateField` serializer필드의 출력을 렌더링하기 위해 기본적으로 사용해야하는 형식 문자열입니다. `None`이면 `DateField` serializer 필드는 Python `date` 객체를 반환하고 날짜 인코딩은 렌더러에 의해 결정됩니다.  

`None`, `'iso-8601'`또는 python [strftime format](https://docs.python.org/3/library/time.html#time.strftime)형식 문자열을 포함하는 list일 수 있습니다.  

Default: `['iso-8601']`

#### `DATE_INPUT_FORMATS`
`DateField` serializer 필드에 대한 입력을 파싱하기 위해 기본적으로 사용해야하는 형식 문자열 list입니다.  

문자열 `'iso-8601'`또는 python [strftime format](https://docs.python.org/3/library/time.html#time.strftime)형식 문자열을 포함하는 list일 수 있습니다.  

Default: `['iso-8601']`

#### `TIME_FORMAT`
`TimeField` serializer 필드의 출력을 렌더링 할 때 기본저긍로 사용해야하는 형식 문자열입니다. `None` 이면 `TimeField` serializer 필드는 Python `time` 객체를 반환하고 time 인코딩은 렌더러에 의해 결정됩니다.  

`None`, `'iso-8601'`또는 python [strftime format](https://docs.python.org/3/library/time.html#time.strftime)형식 문자열을 포함하는 list일 수 있습니다.   

Default: `['iso-8601']`

#### `TIME_INPUT_FORMATS`
`TimeField` serializer 필드에 대한 입력을 파싱하기 위해 기본적으로 사용해야 하는 형식 문자열 list입니다.  

문자열 `'iso-8601'`또는 python [strftime format](https://docs.python.org/3/library/time.html#time.strftime)형식 문자열을 포함하는 list일 수 있습니다.  

Default: `['iso-8601']`

---

### Encodings

#### `UNICODE_JSON`
`True`로 설정하면, JSON response가 response에 유니코드 문자를 허용합니다.

```
{"unicode black star":"★"}
```
`False`로 설정하면 JSON response가 다음과 같이 non-ascii 문자를 이스케이프합니다.

```
{"unicode black star":"\u2605"}
```

두 스타일 모두 [RFC 4627]()을 준수하며 구문적으로 유효한 JSON입니다. 유니코드 스타일은 API 응답을 검사할 때보다 사용자에게 친숙한 것으로 선호됩니다.  

Default: `True`

#### `COMPACT_JSON`
`True`로 설정하면 JSON response sms `':'`과 `','`문자 다음에 공백없이 간결한 표현을 반환합니다.

```
{"is_admin":false,"email":"jane@example"}
```
`False`로 설정하면 JSON 응답이 다음과 같이 약간 더 자세한 표현을 반환합니다.

```
{"is_admin": false, "email": "jane@example"}
```
기본 스타일은 [Heroku's API design guidelines](https://github.com/interagent/http-api-design#keep-json-minified-in-all-responses)에 따라 축소 된 응답을 반환하는 것입니다.  

Default: `True`

#### `COERCE_DECIMAL_TO_STRING`
기존 decimal(10진) type을 지원하지 않는 API 표현에서 decimal 오브젝트를 리턴할 때, 일반적으로 값을 문자열로 리턴하는 것이 가장 좋습니다. 따라서 바이너리 부동 소수점 구현에서 발생하는 정밀도의 손실을 피할 수 있습니다.  
`True`로 설정하면 serializer `DecimalField` 클래스가 Decimal 객체 대신 문자열을 반환합니다. `False`로 설정하면, serializer는 Decimal 객체를 반환합니다. 이 객체는 기본 JSON 인코더가 float으로 반환합니다.

Default: `True`

---

### View names and descriptions
**다음 설정은 `OPTIONS` 요청에 대한 응답 및 Browsable API에서 사용되는 것과 같이 뷰 이름 및 설명을 생성하는데 사용됩니다.**

#### `VIEW_NAME_FUNCTION`
뷰 이름을 생성할 때 사용해야하는 함수를 나타내는 문자열입니다.  
이것은 다음 시그니처가 있는 함수이어야 합니다.

```
view_name(cls, suffix=None)
```

- `cls` : 뷰 클래스. 일반적으로 이름 함수는 `cls.__name__`에 액서스하여 설명적인 이름을 생성 할 때 클래스 이름을 검사합니다.
- `suffix` : viewset에서 개별 뷰를 구별 할 때 사용되는 선택적 suffix

Default: `'rest_framework.views.get_view_name'`

#### `VIEW_DESCRIPTION_FUNCTION`
뷰 설명을 생성 할 때 사용해야하는 함수를 나타내는 문자열입니다.  
기본 설정 값 이외의 태그 스타일을 지원하도록 이 설정을 변경할 수 있습니다. 예를 들어, 브라우저에서 볼 수 있는 API로 출력되는 뷰 문서 문자열의 `rst` 마크업을 지원하는데 사용할 수 있습니다.  
이것은 다음 시그니처가 있는 함수이어야 합니다.

```
view_description(cls, html=False)
```

- `cls` : 뷰 클래스. 일반적으로 설명 함수는 `cls.__doc__`에 액서스하여 설명을 생성 할 때 클래스의 문서화 문자열을 검사합니다.

- `html` : HTML 출력이 필요한지 나타내는 boolean입니다. 탐색 가능한 API에서 사용되면 `True`이고, `OPTIONS`응답을 생성하는데 사용되면 `False`입니다.

Default: `'rest_framework.views.get_view_description'`

### HTML Select Field cutoffs
Browsable API에서 [관계형 필드를 렌더링하기 위한 선택 필드 컷오프](http://www.django-rest-framework.org/api-guide/relations/#select-field-cutoffs)에 대한 전역 설정입니다.

#### `HTML_SELECT_CUTOFF`
`html_cutoff`값의 전역 설정입니다. 정수이어야 합니다.  

Default: 1000

#### `HTML_SELECT_CUTOFF_TEXT`
`html_cutoff_text`의 전역 설정을 나타내는 문자열입니다.  

Default: `"More than {count} items..."`

---

### Miscellaneous settings

#### `EXCEPTION_HANDLER`
지정된 예외에 대한 응답을 반환할 때 사용해야하는 함수를 나타내는 문자열입니다. 이 함수가 `None`을 반환하면 500 error가 발생합니다.  
이 설정은 기본 `{"detail": "Failure..."}`응답 이외의 오류 응답을 지원하도록 변경할 수 있습니다. 예를 들어 `{"errors": [{"message": "Failure...", "code": ""} ...]}`와 같은 API 응답을 제공하는데 사용할 수 있습니다.  

이것은 다음 시그니처가 있는 함수이어야 합니다.

```
exception_handler(exc, context)
```

- `exc` : 예외

Default: `'rest_framework.views.exception_handler'`  

#### `NON_FIELD_ERRORS_KEY`
특정 필드를 참조하지 않고 일반적인 오류인 serializer 오류에 사용해야하는 키를 나타내는 문자열입니다.  

Default: `'non_field_errors'`  

#### `URL_FIELD_NAME`
`HyperlinkedModelSerializer`에 의해 생성 된 URL 필드에 사용해야하는 키를 나타내는 문자열입니다.  

Default: `'url'`

#### `NUM_PROXIES`
API가 실행되는 응용 프로그램 프록시 수를 지정하는데 사용할 수 있는 0 이상의 정수입니다. 이렇게 하면 throttling을 통해 클라이언트 IP 주소를 보다 정확하게 식별할 수 있습니다. `None`으로 설정하면 덜 엄격한 IP 매칭이 throttle 클래스에서 사용됩니다.  

Default: `None`
