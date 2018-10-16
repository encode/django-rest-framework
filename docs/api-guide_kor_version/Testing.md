# Django REST Framework - Testing

_**"Code without tests is broken as designed."  
"테스트가 없는 코드는 의도 한대로 작동하지 않는다." - Jacob Kaplan-Moss**_

REST 프레임워크는 Django의 기존 테스트 프레임워크를 확장하고, API Requests 작성에 대한 지원을 향상시키는 서포트 클래스를 포함하고 있습니다.

## APIRequestFactory
Django의 기존 `RequestFactory` 클래스를 확장합니다.

### Creating test requests
`APIRequestFactory` 클래스는 Django의 표준 `RequestFactory` 클래스와 거의 동일한 API를 지원합니다. 즉 표준 `.get()`, `.post()`, `.put()`, `.patch()`, `.delete()`, `.head()` 및 `.options()` 메서드를 모두 사용할 수 있습니다.

```
rom rest_framework.test import APIRequestFactory

# 표준 `RequestFactory` API을 사용ㅎ여 POST request form을 만든다.
factory = APIRequestFactory()
request = factory.post('/notes/', {'title': 'new idea'})
```

#### Using the `format` argument
`post`,`put`,`patch`와 같은 requests를 만드는 메서드에는 content type을 사용하여 requests를 쉽게 생성 할 수 있도록 하는 argument가 포함되어 있습니다.

```
# Create a JSON POST request
factory = APIRequestFactory()
request = factory.post('/notes/', {'title': 'new idea'}, format='json')
```

기본적으로 사용 가능한 형식은 `multipart`와 `json`입니다. Django의 기존 `RequestFactory`와의 호환성을 위해 기본 형식은 `multipart`입니다.

더 많은 형식에 대한 정보는 [configuration section](http://www.django-rest-framework.org/api-guide/testing/#configuration)을 참조하세요.

#### Explicitly encoding the request body
request 본문을 명시적으로 인코딩해야 하는 경우 `context_type` 플래그를 설정하여 request 본문을 인코딩할 수 있습니다.

```
request = factory.post('/notes/', json.dumps({'title': 'new idea'}), content_type='application/json')
```

#### PUT and PATCH with form data
Django의 `RequestFactory`와 REST 프레임 워크의 `APIRequestFactory` 사이에 주목할 만한 차이점은 다중 파트 양식 데이터가 `.post()` 이외의 메소드로 인코딩된다는 것입니다.

예를 들어, `APIRequestFactory`를 사용하면 다음과 같이 `put`요청을 할 수 있습니다.

```
factory = APIRequestFactory()
request = factory.put('/notes/547/', {'title': 'remember to email dave'})
```

Django의 `RequestFactory`를 사용하면 명시적으로 데이터를 직접 인코딩해야합니다.

```
from django.test.client import encode_multipart, RequestFactory

factory = RequestFactory()
data = {'title': 'remember to email dave'}
content = encode_multipart('BoUnDaRyStRiNg', data)
content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
request = factory.put('/notes/547/', content, content_type=content_type)
```

#### Forcing authentication
`RequestFactory`를 사용하여 직접 뷰를 테스트 할 때는 인증자격 증명을 작성하지않고 직접 자격요청을 인증하는 것이 편리합니다.

강제 요청을 인증하려면 `force_authenticate()` 메소드를 사용하십시오.

```
from rest_framework.test import force_authenticate

factory = APIRequestFactory()
user = User.objects.get(username='olivia')
view = AccountDetail.as_view()

# Make an authenticated request to the view...
request = factory.get('/accounts/django-superstars/')
force_authenticate(request, user=user)
response = view(request)
```

이 메소드의 서명은 `force_authenticate(request, user = None, token = None)`입니다. 전화를 걸 때 사용자와 토큰 중 하나 또는 둘 모두가 설정 될 수 있습니다.

예를 들어, 토큰을 사용하여 강제로 인증하는 경우 다음과 같이 할 수 있습니다.

```
user = User.objects.get(username='olivia')
request = factory.get('/accounts/django-superstars/')
force_authenticate(request, user=user, token=user.token)
```

---

**Note** : `APIRequestFactory`를 사용할 때 반환되는 객체는 Django의 표준 `HttpRequest`이며, REST 프레임워크의 Request 객체는 아니며 뷰가 호출 된 후에만 ​​생성됩니다.  
즉, request 객체에 직접 속성을 설정하면 항상 원하는 결과를 얻을 수 없을 수도 있습니다.  
예를 들어, `.token`을 직접 설정해도 아무 효과도 없으며 세선 인증을 사용하는 경우 `.user`를 직접 설정할 수 있습니다.

```
# Request은`SessionAuthentication`이 사용 중일 때에 만 인증합니다.
request = factory.get('/accounts/django-superstars/')
request.user = user
response = view(request)
```

---

#### Forcing CSRF validation
기본적으로 `APIRequestFactory`으로 생성 된 request에는 REST 프레임워크 뷰에 전달 될 때 CSRF 유효성 검사가 적용되지 않습니다.
CSRF 유효성 검사를 명시적으로 수행해야하는 경우, 팩토리를 인스턴스화 할 때 `enforce_csrf_checks` 플래그를 설정하면됩니다.

```
factory = APIRequestFactory(enforce_csrf_checks=True)
```

---

**Note** : Django의 표준 `RequestFactory`는 이 옵션을 포함할 필요가 없다는 사실에 주목해야 합니다. Django를 사용할 때 뷰를 직접 테스트 할 때 실행되지 않는 미들웨어에서 CSRF 유효성 검사가 수행되기 때문입니다. REST 프레임워크를 사용할 때 뷰 내부에서 CSRF 유효성 검사가 수행되므로 요청 팩토리는 뷰 수준의 CSRF 검사를 비활성화해야합니다.

---

### APIClient
Django의 기존 `Client`클래스를 확장합니다.

#### Making requests
`APIClient`클래스는 DJango의 표준 Client클래스와 동일한 요청 인터페이스를 지원합니다. 즉, `.get()`, `.post()`, `.put()`, `.patch()`, `.delete()`, `.head()`, `.options()` 메서드를 모두 사용할 수 있습니다.

```
from rest_framework.test import APIClient

client = APIClient()
client.post('/notes/', {'title': 'new idea'}, format='json')
```
더 만은 정보는 [configuration section](http://www.django-rest-framework.org/api-guide/testing/#configuration)를 참조하세요.

#### Authenticating

##### .login(**kwargs)
`login`메소드는 Django의 `Cilent`클래스와 똑같이 작동합니다. 이렇게 하면 `SessionAuthentication`이 포함된 모든 views에 대한 요청을 인증 할 수 있습니다.

```
# Make all requests in the context of a logged in session.
client = APIClient()
client.login(username='lauren', password='secret')
```
로그아웃하려면 `logout`메소드를 호출하세요.

```
# Log out
client.logout()
```
`login` 메소드는 `AJAX API`와의 상호 작용을 포함하는 웹 사이트와 같이 세션 인증을 사용하는 API를 테스트하는데 적합합니다.

##### .credentials(**kwargs)
`credentials`메소드는 테스트 클라이언트가 모든 후속 요청에 포함 할 헤더를 설정하는데 사용할 수 있습니다.

```
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

# Include an appropriate `Authorization:` header on all requests.
token = Token.objects.get(user__username='lauren')
client = APIClient()
client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
```
`credentials`를 다시 호출하면 기존 `credentials`을 덮어 씁니다. 인수없이 메서드를 호출하여 기존 `credentials`의 설정을 해제할 수 있습니다.

```
# Stop including any credentials
client.credentials()
```
`credentials` 방법은 기본인증, OAuth1a과 OAuth2 인증 및 간단한 토큰 인증스키마와 같은 인증 헤더가 필요한 API를 테스트하는데 적합합니다.

##### .force_authenticate(user=None, token=None)
때로는 인증을 생략하고 테스트 클라이언트의 모든 요청을 인증 된 것으로 자동처리하도록 할 수 있습니다.

이는 API를 테스트하고 있지만 테스트 요청을 하기 위해 유효한 자격 증명을 작성하지 않으려는 경우 유용한 단축키입니다.

```
user = User.objects.get(username='lauren')
client = APIClient()
client.force_authenticate(user=user)
```
후속 요청을 인증 해제하려면 `force_authenticate`를 호출하여 사용자/토큰을 `None`으로 설정하세요.

```
client.force_authenticate(user=None)
```

#### CSRF validation
기본적으로 CSRF 유효성 검사는 APICLient를 사용할 떄 적합하지 않습니다. CSRF 유효성 검사를 명시적으로 활성화해야하는 경우 Client를 인스턴스화 할때 `enforce_csrf_checks`플래그를 설정하면 됩니다.

```
client = APIClient(enforce_csrf_checks=True)
```
평소처럼 CSRF 유효성검사는 세션 인증 된 views에만 적용됩니다. 즉, 클라이언트가 `login()`을 호출하려 로그인한 경우에만 CSRF 유효성 검사가 수행됩니다.

---

### RequestsClient
RESR 프레임워크에는 `request`(Python 라이브러리)를 사용하여 애플리케이션과 상호 작용하는 client도 포함되어 있습니다. 다음과 같은 경우 유용하게 사용할 수 있습니다.

- 주로 다른 Python 서비스의 API와의 인터페이스를 기대하고 있으며, client가 볼 수 있는 것과 동일한 수준에서 서비스를 테스트하려 할 때
- 준비 또는 실제 환경에 대해 실행할 수 있는 방식으로 테스트를 작성할 때 ("Live test" 참조)

이는 requests 세션을 직접 사용하는 것과 동일한 인터페이스를 제공합니다.

```
client = RequestsClient()
response = client.get('http://testserver/users/')
assert response.status_code == 200
```
requests client에서는 정규화 된 URL을 전달해야 합니다.

#### `RequestsClient` and working with the database
`RequestsClient`클래스는 서비스 인터페이스만 상호 작용하는 테스트를 작성하려는 경우에 유용합니다. 이것은 Django 테스트 클라이언트를 사용하는 것보다 조금 더 엄격합니다. 모든 상호작용이 API를 통해 이루어져야하기 떄문입니다.
`RequestsClient`를 사용하는 경우 데이터베이스 모델과 직접 상호 작용하는 대신 테스트 설정 및 결과 주장(?)을 일반 API 호출로 수행해야합니다.
예를 들어, `Customer.objects.count () == 3`를 확인하는 대신 `customers` 마지막점을 나열하고 3개의 레코드가 있는지 확인하세요.

#### Headers & Authentication
custom 헤더와 인증자격 증명은 `requests.Session` 인스턴스를 사용할 때와 동일한 방식으로 제공 될 수 있습니다.

```
from requests.auth import HTTPBasicAuth

client.auth = HTTPBasicAuth('user', 'pass')
client.headers.update({'x-test': 'true'})
```

#### CSRF
`SessionAuthentication`을 사용하는 경우 `POST`, `PUT`, `PATCH`, `DELETE` 요청에 대해 CSRF 토큰을 포함해야합니다.
JavaScript 기반의 클라이언트가 사용하는 것과 동일한 흐름으로 수행 할 수 있습니다.  
먼저 CRSF 토큰을 얻기 위해 `GET` 요청을 하고 다음 요청에 토큰을 제시하십시오.

```
client = RequestsClient()

# Obtain a CSRF token.
response = client.get('/homepage/')
assert response.status_code == 200
csrftoken = response.cookies['csrftoken']

# Interact with the API.
response = client.post('/organisations/', json={
    'name': 'MegaCorp',
    'status': 'active'
}, headers={'X-CSRFToken': csrftoken})
assert response.status_code == 200
```
#### Live tests
신중하게 사용하면 `RequestsClient`와 `CoreAPIClient`가 모두 개발 환경에서 실행되거나 준비 서버 또는 프로덕션 환경에 직접 실행 될 수 있는 테스트 사례를 작성할 수 있습니다.
이럼 스타일로 몇 가지 핵심 기능 중 일부에 대한 기본 테스트를 만드는 것은 실제 서비스를 확인하는 강력한 방법입니다. 이렇게하려면 테스트가 고객 데이터에 직접 영향을 주지 않는 방식으로 실행되도록 설정 및 해제하는데 신중을 기해야합니다.

---

### CoreAPIClient
`CoreAPIClient`를 사용하면 `coreapi` (Python 클라이언트 라이브러리)를 사용하여 API와 상호 작용할 수 있습니다.

```
# Fetch the API schema
client = CoreAPIClient()
schema = client.get('http://testserver/schema/')

# Create a new organisation
params = {'name': 'MegaCorp', 'status': 'active'}
client.action(schema, ['organisations', 'create'], params)

# Ensure that the organisation exists in the listing
data = client.action(schema, ['organisations', 'list'])
assert(len(data) == 1)
assert(data == [{'name': 'MegaCorp', 'status': 'active'}])
```

#### Headers & Authentication
Customs 헤더와 인증은 `RequestsClient`와 비슷한 방식으로 `CoreAPIClient`와 함께 사용할 수 있습니다.

```
from requests.auth import HTTPBasicAuth

client = CoreAPIClient()
client.session.auth = HTTPBasicAuth('user', 'pass')
client.session.headers.update({'x-test': 'true'})
```

---

### Test cases
REST 프레임워크는 DJango 테스트 케이스 클래스를 반영하지만, Django의 기본 클라이언트 대신 `APIClient`를 사용하는 테스트 케이스 클래스를 포함합니다.

- APISimpleTestCase
- APITransactionTestCase
- APITestCase
- APILiveServerTestCase

#### Example]
Django 테스트케이스 클래스처럼 REST 프레임워크의 테스트 케이스 클래스 중 하나를 사용할 수 있습니다. `self.client` 속성은 `APIClient` 인스턴스입니다.

```
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from myproject.apps.core.models import Account

class AccountTests(APITestCase):
    def test_create_account(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('account-list')
        data = {'name': 'DabApps'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Account.objects.get().name, 'DabApps')
```

---

### Testing responses

#### Checking the response data
테스트 응답의 유효성을 검사 할 때 완전히 렌더링 된 응답을 검사하는 것보다 응답이 생성 된 데이터를 검사하는 것이 더 편리합니다.

예를 들어, `response.data`를 검사하는 것이 더 쉽습니다.

```
response = self.client.get('/users/4/')
self.assertEqual(response.data, {'id': 4, 'username': 'lauren'})
```

`response.content`를 구문 분석한 결과를 검사하는 대신:

```
response = self.client.get('/users/4/')
self.assertEqual(json.loads(response.content), {'id': 4, 'username': 'lauren'})
```

#### Rendering responses
`APIRequestFactory`를 사용하여 뷰를 직접 테스트하는 경우, 템플릿 응답의 렌더링이 Django의 내부 requests - response 에 의해 수행되기 때문에 반환되는 응답은 아직 렌더링되지 않습니다. `response.content`에 액세스하려면 먼저 응답을 렌더링해야합니다.

```
view = UserDetail.as_view()
request = factory.get('/users/4')
response = view(request, pk='4')
response.render()  # Cannot access `response.content` without this.
self.assertEqual(response.content, '{"username": "lauren", "id": 4}')
```

---

### Configuration

#### Setting the default format
테스트 요청을하는 데 사용되는 기본 형식은 `TEST_REQUEST_DEFAULT_FORMAT` 설정 키를 사용하여 설정할 수 있습니다. 예를 들어, 테스트 요청을 항상 `JSON`을 사용하려면 `settings.py`파일에서 다음을 설정하세요.

```
REST_FRAMEWORK = {
    ...
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}
```

#### Setting the available formats
multipart 또는 `json` 요청 이외의 것을 사용하여 요청을 테스트해야하는 경우 `TEST_REQUEST_RENDERER_CLASSES` 설정을 설정하여 요청을 테스트 할 수 있습니다.

예를 들어, 테스트 요청에 `format = 'html'`을 추가하려면 `settings.py` 파일에 다음과 같은 내용이 추가합니다.

```
REST_FRAMEWORK = {
    ...
    'TEST_REQUEST_RENDERER_CLASSES': (
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.TemplateHTMLRenderer'
    )
}
```