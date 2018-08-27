# Django REST Framework - Versioning

---

_"Versioning an interface is just a "polite" way to kill deployed clients."_  

_"인터페이스의 버전 관리는 배치 된 클라이언트를 죽이는 "정중한" 방법 일 뿐입니다."_  

_— Roy Fielding._

---

## Versioning (버전관리)
API 버전 관리를 통해 서로 다른 클라이언트 간의 동작을 변경할 수 있습니다. REST 프레임워크는 다양한 버전 관리 체계를 제공합니다.  
버전 지정은 수신 클라이언트 요청에 의해 결정되며 request URL을 기반으로하거나 request 헤더를 기반으로 할 수 있습니다.  
버전 관리에 접근하는데는 여러가지 유효한 방법이 있습니다. 특히 버전을 벗어난 여러 클라이언트를 가진 매우 장기적인 시스템을 엔지니어링하는 경우에는 [버전이 없는 시스템도 적합](https://www.infoq.com/articles/roy-fielding-on-versioning)할 수 있습니다.

### Versioning with REST framework
API 버전 관리가 활성화되면 `request.version`속성에는 들어오는 클라이언트 request에서 요청 된 버전에 해당하는 문자열이 포함됩니다.  
기본적으로 버전 관리는 활성화되어있지 않으며 `request.version`은 항상 `None`을 반환합니다.

#### Varying behavior based on the version
API동작을 변경하는 방법은 우리에게 달려있지만 일반적인 한가지 예는 최신 버전의 다른 serializer 스타일로 전환하는 것입니다. 예:

```python
def get_serializer_class(self):
    if self.request.version == 'v1':
        return AccountSerializerVersion1
    return AccountSerializer
```

#### Reversing URLs for versioned APIs
REST 프레임워크에 포함 된 역순 함수는 버전 관리체계와 관련되어 있습니다. 현재 request를 키워드 인수로 포함시켜야 합니다.

```python
from rest_framework.reverse import reverse

reverse('bookings-list', request=request)
```
위의 함수는 요청 버전에 적합한 모든 URL 변환을 적용합니다. 예:

- `NamespacedVersioning`이 사용되고 API 버전이 'v1'인 경우 사용 된 URL 조회는 `http://example.org/v1/bookings/`과 같은 URL로 해석 될 수있는 `'v1 : bookings-list'`입니다.
- `QueryParameterVersioning`이 사용되고 API 버전이 `1.0` 인 경우 반환 된 URL은 `http://example.org/bookings/?version=1.0`과 같을 수 있습니다.

#### Versioned APIs and hyperlinked serializers
하이퍼 링크 된 serializer 스타일을 URL 기반 버전 관리 scheme와 함께 사용하는 경우 해당 요청을 컨텍스트로 serializer에 포함해야 합니다.

```python
def get(self, request):
    queryset = Booking.objects.all()
    serializer = BookingsSerializer(queryset, many=True, context={'request': request})
    return Response({'all_bookings': serializer.data})
```
이렇게 하면 반환 된 모든 URL에 적절한 버전이 포함될 수 있습니다.

### Configuring the versioning scheme
버전 관리 scheme는 `DEFAULT_VERSIONING_CLASS`설정 키로 정의됩니다.

```python
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning'
}
```
명시적으로 설정하지 않으면 `DEFAULT_VERSIONING_CLASS`의 값은 `None`이 됩니다. 이 경우 `request.version` 속성은 항상 `None`을 반환합니다.  
개별 view에서 versioning scheme를 설정할 수도 있습니다. 일반적으로 전역적으로 single versioning scheme를 사용하는 것이 더 합리적이므로 이 작업을 수행할 필요가 없습니다. 그렇게 해야한다면 `versioning_class` 속성을 사용하세요.

```python
class ProfileList(APIView):
    versioning_class = versioning.QueryParameterVersioning
```

#### Other versioning settings
다음 설정 키는 versioning를 제어하는데도 사용됩니다.

- `DEFAULT_VERSION` : 버전 정보가 없는 경우 `request.version`에 사용해야 하는 값입니다. 기본값은 `None`입니다.
- `ALLOWED_VERSIONS` : 이 값을 설정하면 versioning scheme에서 반환 할 수 있는 버전 집합이 제한되며 제공된 버전이 이 집합에 없는 경우 오류가 발생합니다. `DEFAULT_VERSION` 설정에 사용 된 값은 항상 `ALLOWED_VERSIONS`  set의 일부로 간주됩니다 (단, `None`이 아닌 경우). 기본값은 `None`입니다.
- `VERSION_PARAM` : 미디어 유형 또는 URL 쿼리 parameter와 같이 모든 버전 지정 parameter에 사용해야하는 문자열입니다. 기본값은 `'version'`입니다.

또한 고유한 versioning scheme를 정의하고 `default_version`, `allowed_version` 및 `version_param`클래스 변수를 사용하여 버전 별 또는 뷰 set 별로 세 가지 값을 더한 버전 클래스를 설정할 수 있습니다. 예를 들어, `URLPathVersioning`를 사용하려면 다음과 같이 하십시오.

```python
from rest_framework.versioning import URLPathVersioning
from rest_framework.views import APIView

class ExampleVersioning(URLPathVersioning):
    default_version = ...
    allowed_versions = ...
    version_param = ...

class ExampleView(APIVIew):
    versioning_class = ExampleVersioning
```

---

## API Reference

### AcceptHeaderVersioning
이 scheme는 클라이언트가 `Accept` 헤더의 미디어 타입의 일부로 버전을 지정하도록 요구합니다. 이 버전은 기본 미디어 타입을 보완하는 미디어 타입 parameter로 포함됩니다.  
다음 accept 헤더 versioning 스타일을 사용하는 HTTP request의 예입니다.

```
GET /bookings/ HTTP/1.1
Host: example.com
Accept: application/json; version=1.0
```
위의 예제 request에서 `request.version`속성은 `'1.0'`문자열을 반환합니다.  
Accept 헤더에 기반한 versioning는 [일반적](http://blog.steveklabnik.com/posts/2011-07-03-nobody-understands-rest-or-http#i_want_my_api_to_be_versioned)으로 [모범 사례](https://github.com/interagent/http-api-design/blob/master/en/foundations/require-versioning-in-the-accepts-header.md)로 간주되지만 클라이언트 요구 사항에 따라 다른 스타일이 적합할 수도 있습니다.  

#### Using accept headers with vendor media types
엄밀히 말하자면 `json` 미디어 타입은 [추가 parameter](http://tools.ietf.org/html/rfc4627#section-6)를 포함하는 것으로 지정되지 않습니다. 잘 정의 된 공개 API를 작성하는 경우 [vendor media type](https://en.wikipedia.org/wiki/Internet_media_type#Vendor_tree)을 사용하는 것이 좋습니다. 이렇게 하려면 custom 미디어 타입으로 `JSON` 기반 렌더러를 사용하도록 렌더러를 구성하세요.

```python
class BookingsAPIRenderer(JSONRenderer):
    media_type = 'application/vnd.megacorp.bookings+json'
```
클라이언트의 request는 다음과 같습니다.

```
GET /bookings/ HTTP/1.1
Host: example.com
Accept: application/vnd.megacorp.bookings+json; version=1.0
```

### URLPathVersioning
이 스키마는 클라이언트가 URL 경로의 일부로 버전을 지정하도록 요구합니다.  

```
GET /v1/bookings/ HTTP/1.1
Host: example.com
Accept: application/json
```
URL conf에는 `'version'`키워드 인수가 있는 버전과 일치하는 패턴이 포함되어야하므로 이 정보를 versioning scheme에서 사용할 수 있습니다.

```python
urlpatterns = [
    url(
        r'^(?P<version>(v1|v2))/bookings/$',
        bookings_list,
        name='bookings-list'
    ),
    url(
        r'^(?P<version>(v1|v2))/bookings/(?P<pk>[0-9]+)/$',
        bookings_detail,
        name='bookings-detail'
    )
]
```

### NamespaceVersioning
클라이언트에서 이 scheme는 `URLPathVersioning`과 동일합니다. 유일한 차이점은 URL 키워드 인수 대신 URL 네임스페이스를 사용하므로 Django 애플리케이션에서 어떻게 구성되어 있는지입니다.

```
GET /v1/something/ HTTP/1.1
Host: example.com
Accept: application/json
```
이 scheme에서 `request.version`속성은 틀어오는 request 경로와 일치하는 네임스페이스를 기반으로 결정됩니다.  
다음 예제에서는 서로 다른 네임 스페이스 아래에 각각 다른 두가지 URL 접두어가 있는 일련의 view를 제공합니다.

```python
# bookings/urls.py
urlpatterns = [
    url(r'^$', bookings_list, name='bookings-list'),
    url(r'^(?P<pk>[0-9]+)/$', bookings_detail, name='bookings-detail')
]

# urls.py
urlpatterns = [
    url(r'^v1/bookings/', include('bookings.urls', namespace='v1')),
    url(r'^v2/bookings/', include('bookings.urls', namespace='v2'))
]
```

간단한 versioning scheme가 필요하다면 `URLPathVersioning`과 `NamespaceVersioning` 모두 합리적입니다.

### HostNameVersioning
hostname versioning scheme에서는 클라이어튼가 요청된 버전을 URL의 hostname의 일부로 지정해야합니다.  
예를 들어 다음은 `http://v1.example.com/bookings/` URL에 대한 HTTP 요청입니다.

```
GET /bookings/ HTTP/1.1
Host: v1.example.com
Accept: application/json
```
기본적으로 이 구현은 hostname이 다음과 같은 간단한 정규식과 일치 할 것으로 기대합니다.

```
^([a-zA-Z0-9]+)\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+$
```
첫 번째 그룹은 대괄호로 묶여 있으며 hostname의 일치하는 부분임을 나타냅니다.  
일반적으로 `127.0.0.1`과 같은 기존 IP주소에 액서스하므로 `HostNameVersioning` scheme는 디버그 모드에서 사용하기가 어려울 수 있습니다. 이 경우 도움이 될 수 있는 [`custom subdomain`으로 localhost에 액서스](https://reinteractive.com/posts/199-developing-and-testing-rails-applications-with-subdomains)하는 다양한 온라인 서비스가 있습니다.  
hostname versioning scheme는 여러 API 버전에 대해 서로 다른 DNS 레코드를 구성할 수 있으므로 들어오는 request를 버전에 따라 다른 서버로 라우팅해야하는 경우에 특히 유용합니다.

### QueryParameterVersioning
이 스키마는 URL에 쿼리 parameter로 버전을 포함하는 간단한 스타일입니다. 예:

```
GET /something/?version=0.1 HTTP/1.1
Host: example.com
Accept: application/json
```

---

## Custom versioning schemes
custom versioning scheme를 구현하려면 `BaseVersioning`를 서브 클래스화하고 `.determine_version`메서드를 대체하세요.

### Example
다음 예에서는 custom `X-API-Version` 헤거를 사용하여 요청한 버전을 확인합니다.

```python
class XAPIVersionScheme(versioning.BaseVersioning):
    def determine_version(self, request, *args, **kwargs):
        return request.META.get('HTTP_X_API_VERSION', None)
```
versioning scheme가 request URL을 기반으로 하는 경우 버전이 지정된 URL의 결정 방법도 변경해야합니다. 이렇게 하려면 클래스의 `.reverse()`메서드를 오버라이드해야합니다. 예제는 소스코드를 참조하세요.
