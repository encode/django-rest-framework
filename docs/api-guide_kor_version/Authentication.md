# Django REST Framework - Authentication

---

_"Auth needs to be pluggable."_  

_"인증은 플러그가 가능해야 합니다."_  

_— Jacob Kaplan-Moss, "REST worst practices"_

---

## Authentication(입증)
Authentication은 수신 요청을 요청한 사용자 또는 서명 된 토큰과 같은 식별 자격 증명 세트를 연결하는 메커니즘입니다. 그런 다음 [권한](http://www.django-rest-framework.org/api-guide/permissions/)과 [정책](http://www.django-rest-framework.org/api-guide/throttling/)은 이러한 자격 증명을 사용하여 요청을 허용해야 하는지 결정할 수 있습니다.  
REST 프레임워크는 여러가지 인증 스키마를 즉시 제공하며 custom 스키마를 구현할 수도 있습니다.  
Authentication은 항상 View의 맨 처음, 권한 및  제한 검사가 수행되기 전에 그리고 다른 코드가 진행되기 전에 실행됩니다.  
`request.user`속성은 일반적으로 `contrib.auth`패키지의 `User`클래스 인스턴스로 설정됩니다.  
`request.auth` 등록정보는 추가인증 정보에 사용됩니다. 예를 들어, request가 서명 된 인증 토큰을 나타내는데 사용될 수 있습니다.

---

**Note**: 들어오는 request를 허용하거나 거부하지 않는 인증은 request가 수행된 자격 증명을 식별하기만하면 된다는 것을 잊지 마십시오.  
API에 대한 사용권한정책을 설정하는 방법에 대한 자세한 내용은 [permissions documentation](http://www.django-rest-framework.org/api-guide/permissions/)를 참조하세요.

---

### How authentication is determined
인증 체계는 항상 클래스 list으로 정의됩니다. REST 프레임워크는 list의 각 클래스에 대해 인증을 시도하고 성공적으로 인증한 첫 번째 클래스의 반환 값을 사용하여 `request.user` 및 `request.auth`를 설정합니다.  
클래스가 인증되지 않으면 `request.user`는 `django.contrib.auth.AnonymousUser`의 인스턴스로 설정되고 `request.auth`는 `None`으로 설정됩니다.  
인증되지 않은 요청에 대한 `request.user`,  `request.auth`의 값은 `UNAUTHENTICATED_USER`, `UNAUTHENTICATED_TOKEN` 설정을 사용하여 수정할 수 있습니다.

### Setting the authentication scheme
`DEFAULT_AUTHENTICATION_CLASSES` 설정을 사용하여 기본 인증 구성표를 전역으로 설정할 수 있습니다. 예를 들면.

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}
```
또한 `APIVIew` CBV를 사용하여 view 단위 또는 view단위로 인증 체계를 구성할 수 있습니다.

```python
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class ExampleView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        return Response(content)
```
또는 FBV와 함께 `@api_view`데코레이터를 사용하는 경우

```pyhon
@api_view(['GET'])
@authentication_classes((SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def example_view(request, format=None):
    content = {
        'user': unicode(request.user),  # `django.contrib.auth.User` instance.
        'auth': unicode(request.auth),  # None
    }
    return Response(content)
```

### Unauthorized and Forbidden responses(무단 및 금지된 응답)
인증되지 않은 요청에 권한이 거부되면 적절한 두 가지 오류 코드가 있습니다.

- [HTTP 401 Unauthorized](https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.2)
- [HTTP 403 Permission Denied](https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.4)

HTTP 401 응답에는 항상 클라이언트에 인증 방법을 지시하는 `WWW-Authenticate` 헤더가 포함되어야합니다. HTTP 403 응답에는 `WWW-Authenticate` 헤더가 포함되지 않습니다.  
사용되는 response의 종류는 인증 체계에 따라 다릅니다. 여러 인증 스키마가 사용 중일 수 있지만, response의 타입을 결정하는데 하나의 스키마만 사용할 수 있습니다. **view에 설정된 첫번째 authentication 클래스는 response 타입을 결정 할 때 사용됩니다.**  
request가 성공적으로 인증 될 수 있지만, 여전히 request를 수행할 권한이 거부 된 경우, 인증 스키마에 관계없이 `403 Permission Denied`응답이 항상 사용됩니다.

### Apache mod_wsgi specific configuration
mod_wsgi를 사용하여 Apache에 배포한다면, 권한 부여 헤더는 기본적으로 응용프로그램 수준이 아닌 Apache에서 인증을 처리한다고 가정하므로, 기본적으로 WSGI 응용프로그램에 전달되지 않습니다.  
Apache에 배포하고 비 세션 기반 인증을 사용하는 경우 `mod_wsgi`를 명시적으로 구성하여 필요한 헤더를 응용프로그램에 전달해야 합니다. 이는 적절한 컨텍스트에서 `WSGIPassAuthorization`지시문을 지정하고 `On`으로 설정하여 수행할 수 있습니다.

```
# 이것은 서버 설정, 가상 호스트, 디렉토리 또는 .htaccess 중 하나에 들어갈 수 있습니다.

WSGIPassAuthorization On
```

---

## API Reference

### BasicAuthentication
이 인증 체계는 사용자의 사용자 이름과 암호에 대해 서명 된 [HTTP basic Authentication](https://tools.ietf.org/html/rfc2617)을 사용합니다. 기본 인증은 일반적으로 테스트에만 적합합니다.  
성공적으로 인증되면 `BasicAuthencation`은 다음 자격 증명을 제공합니다.

- `request.user`는 Django `User`인스턴스가 될 것입니다.
- `request.auth`는 `None`입니다.

권한이 거부 된 인증되지 않은 응답은 적절한 WWW-Authenticate 헤더와 함께 `HTTP 401 Unauthorized` 웅답이 됩니다.

```
WWW-Authenticate: Basic realm="api"
```

**Note**: 프로덕션 환경에서 `BasicAuthentication`을 사용하는 경우 `https`를 통해서만 API를 사용할 수 있어야 합니다. 또한 API 클라이언트가 로그인 할때 항상 사용자 이름과 비밀번호를 다시 요청하고 해당 세부정보를 영구 저장소에 저장하지 않도록 해야합니다.

### TokenAuthentication
이 인증체계는 간단한 토큰 기반 HTTP인증체계를 사용합니다. 토큰 인증은 네이티브 데스크톱 및 모바일 클라이언트와 같은 클라이언트 - 서버 설정에 적합합니다.  
`TokenAuthentication` 스키마를 사용하려면 `TokenAuthentication`을 포함하도록 [authentication클래스를 구성](http://www.django-rest-framework.org/api-guide/authentication/#setting-the-authentication-scheme)하고 `INSTALLED_APPS`설정에 `rest_framework.authtoken`를 추가해야 합니다.

```
INSTALLED_APPS = (
    ...
    'rest_framework.authtoken'
)
```

---

**Note**: 설정을 변경한 후에 `manage.py migrate`를 실행해야합니다. `rest_framework.authtoken`앱은 Django 데이터베이스 마이그레이션을 제공합니다.

---

또한 사용자를 위한 토큰을 만들어야 합니다.

```python
from rest_framework.authtoken.models import Token

token = Token.objects.create(user=...)
print token.key
```
클라이언트가 인증하려면 토큰 키가 `Authorization` HTTP 헤더에 포함되어야합니다. 키에는 두 문자열을 공백으로 구분하여 문자열 리터럴 "Token"을 prefix로 사용해야합니다. 예:

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```
**Note**: `Bearer`와 같은 헤더에 다른 키워드를 사용하려면 단순히 `TokenAuthentication`을 서브 클래스화하고 `keyword` 클래스 변수를 설정하십시오.  
성공적으로 인증되면 `TokenAuthentication`은 다음 자격 증명을 제공합니다.

- `request.user`는 Django `User` 인스턴스가 될 것입니다.
- `request.auth`는 `rest_framework.authtoken.models.Token` 인스턴스가 됩니다.

권한이 거부 된 인증되지 않은 응답은 적절한 WWW-Authenticate 헤더와 함께 `HTTP 401 Unauthorized` 응답이 됩니다. 예:

```
WWW-Authenticate: Token
```
`curl` command line tool은 토큰으로 인증된 API를 테스트 하는데 유용할 수 있습니다. 예:

```
curl -X GET http://127.0.0.1:8000/api/example/ -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'
```

---
**Note**: 프로덕션 환경에서 `TokenAuthentication`을 사용하는 경우 `https`를 통해서만 API를 사용할 수 있어야 합니다.

---
#### Generating Tokens
##### By using signals
모든 사용자가 자동으로 생선 된 토큰을 갖기를 원하면 사용자의 `post_save`신호를 간단히 잡을 수 있습니다.

```python
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
```
이 코드는 snippet이 설치된 `models.py` 모듈이나 시작시 Django가 가져올 다른 위치에 배치해야 합니다.  
이미 일부 사용자를 만든 경우 다음과 같이 모든 기존 사용자에 대한 토큰을 생성 할 수 있습니다.

```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

for user in User.objects.all():
    Token.objects.get_or_create(user=user)
```
##### By exposing an api endpoint(api 엔드포인트를 노출시킴)
`TokenAuthentication`을 사용할 때 클라이언트가 사용자 이름과 암호가 있는 토큰을 얻을 수 있는 메커니즘을 제공 할 수 있습니다. REST 프레임워크는 이 동작을 제공하는  built-in 뷰를 제공합니다. 그것을 사용하려면 URLconf에 `obtain_auth_token` 뷰를 추가하세요.

```python
from rest_framework.authtoken import views
urlpatterns += [
    url(r'^api-token-auth/', views.obtain_auth_token)
]
```
패턴의 URL 부분은 원하는대로 사용할 수 있습니다.  
`obtain_auth_token` 뷰는 유효한 `사용자 이름` 및 `암호` 필드가 양식 데이터 또는 JSON을 사용하여 뷰에 POST되면 JSON 응답을 리턴합니다.

```
{ 'token' : '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' }
```
기본 `obtain_auth_token` 뷰는 설정에서 기본 renderer 및 parser 클래스를 사용하는 대신 JSON 요청 및 응답을 명시적으로 사용합니다.
`obtain_auth_token`view의 custom 된 버전이 필요하면 `ObtainAuthToken`view 클래스를 대체하고 URL conf에 대신 사용하세요.  
기본적으로 `obtain_auth_token` view에 적용된 사용 권한이나 제한이 없습니다. 제한을 적용하려면 view클래스를 재정의하고 `throttle_classes`속성을 사용하여 view클래스를 포함해야 합니다.

##### With Django admin
관리자 인터페이스를 통해 수동으로 토큰을 생성 할 수도 있습니다. 대규모 사용자 기반을 사용하는 경우, `user` 필드를 `raw_field`로 선언하여 `TokenAdmin` 클래스를 monkey 패치하여 필요에 맞게 custom하는 것이 좋습니다.

`your_app/admin.py`:

```python
from rest_framework.authtoken.admin import TokenAdmin

TokenAdmin.raw_id_fields = ('user',)
```

### SessionAuthentication
이 인증방식은 Django의 기본 세션 백엔드를 인증에 사용합니다. 세션 인증은 웹 사이트롸 동일한 세션 컨텍스트에서 실행되는 AJAX 클라이언트에 적합합니다.  
성공적으로 인증되면 `SessionAuthentication`은 다음 자격 증명을 제공합니다.

- `request.use`r는 Django `User` 인스턴스가 될 것입니다.
- `request.auth`는 `None`입니다.

권한이 거부 된 인증되지 않은 응답은 `HTTP 403 Forbidden`응답이 됩니다.  
SessionAuthentication과 함께 AJAX 스타일 API를 사용하는 경우 `PUT`, `PATCH`, `POST` 또는 `DELETE` 요청과 같은 **"안전하지 않은"**HTTP 메소드 호출에 유효한 CSRF 토큰을 포함시켜야합니다. 자세한 내용은 [Django CSRF documentation](https://docs.djangoproject.com/en/1.10/ref/csrf/#ajax) 참조  
**Warning**: 로그인 페이지를 만들 때 항상 Django의 표준 로그인 view를 사용하세요. 이렇게 하면 로그인view가 올바르게 보호됩니다.  
REST 프레임워크의 CSRF 유효성 검사는 동일한 view에 대해 session 및 non-session 기반 인증을 모두 지원해야하므로 표준 Django와 약간 다르게 작동합니다. 즉, 인증 된 요청만 CSRF 토큰이 필요로 하며 익명 요청은 CSRF 토큰 없이 전송될 수 있습니다. 이 동작은 항상 CSRF 유효성 검사가 적용된 로그인 View에는 적합하지 않습니다.

## Custom authentication
사용자 정의 인증 체계를 구현하려면 `BaseAuthentication`을 서브 클래스화하고 `.authenticate(self, request)` 메소드를 대체하십시오. 이 메소드는 인증에 성공하면 2-tuple(user, auth)을 반환하고, 그렇지 않으면 `None`을 반환햐야 합니다.  
`None`을 반환하는 대신 상황에 따라 `.authenticate()` 메서드에서 `AuthenticationFailed` 예외를 발생 시킬 수 있습니다.  
일반적으로 취해야 할 접근 방식은 다음과 같습니다.

- 인증을 시도하지 않으면 `None`을 반환합니다. 사용중인 다른 인증 체계도 계속 검사됩니다.
- 인증을 시도했지만 실패한 경우 `AuthenticationFailed` 예외를 발생시킵니다. 권한 확인과 관계없이 다른 인증 스키마를 확인하지 않고 즉시 오류 응답이 반환됩니다.  

또한 `.authenticate_header(self, request)` 메소드를 대체 할 수 있습니다. 구현 된 경우 `HTTP 401 Unauthorized` 응답에서 `WWW-Authenticate` 헤더의 값으로 사용 될 문자열을 반환해야합니다.  
`.authenticate_header()` 메소드가 대체되지 않으면, 인증 스키마는 인증되지 않은 요청이 액세스를 거부 할 때 `HTTP 403 Forbidden` 응답을 리턴합니다.

### Example
다음 예제는 들어오는 요청을 'X_USERNAME'이라는 사용자 지정 request 헤더에서 사용자 이름으로 지정된 사용자로 인증합니다.

```python
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

class ExampleAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        username = request.META.get('X_USERNAME')
        if not username:
            return None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user')

        return (user, None)
```

## Third party packages
다음의 타사 패키지도 제공됩니다.

### Django OAuth Toolkit
[Django OAuth Toolkit](https://github.com/evonove/django-oauth-toolkit) 패키지는 OAuth 2.0 지원을 제공하며 Python 2.7 및 Python 3.3 이상에서 작동합니다. 이 패키지는 [Evonove](https://github.com/evonove/)에서 유지 관리하며 우수한 [OAuthLib](https://github.com/idan/oauthlib)을 사용합니다. 이 패키지는 잘 문서화되어 잘 지원되며 현재 **OAuth 2.0 지원을위한 권장 패키지**입니다.

#### 설치와 구성
pip를 사용하여 설치합니다.

```
pip install django-oauth-toolkit
```
패키지를 `INSTALLED_APPS`에 추가하고 REST 프레임워크 설정을 수정하십시오.

```
INSTALLED_APPS = (
    ...
    'oauth2_provider',
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
    )
}
```
자세한 내용은 [Django REST framework - Getting started](https://django-oauth-toolkit.readthedocs.io/en/latest/rest-framework/getting_started.html)를 참조하세요.

### Django REST framework OAuth
Django [REST 프레임워크 OAuth](http://jpadilla.github.io/django-rest-framework-oauth/) 패키지는 REST 프레임워크에 대한 OAuth1 및 OAuth2 지원을 제공합니다. 이 패키지는 이전에 REST 프레임 워크에 직접 포함되었지만 이제는 타사 패키지로 지원 및 유지 관리됩니다.
#### 설치와 구성
pip를 사용하여 패키지를 설치합니다.

```
pip install djangorestframework-oauth
```
설정과 사용에 대한 자세한 내용은 Django REST 프레임워크 OAuth문서에서 [인증](http://jpadilla.github.io/django-rest-framework-oauth/authentication/)과 [권한](http://jpadilla.github.io/django-rest-framework-oauth/permissions/)을 참조하세요.

### Digest Authentication
HTTP 다이제스트 인증은 HTTP 기본 인증을 대체하기 위한 것으로 널리 구현 된 구성이며 간단한 암호화 된 인증 메커니즘을 제공합니다. [Juan Riaza](https://github.com/juanriaza)는 REST 프레임워크에 HTTP 다이제스트 인증 지원을 제공하는 [djangorestframework-digestauth](https://github.com/juanriaza/django-rest-framework-digestauth) 패키지를 유지 관리합니다.

### Django OAuth2 Consumer
[Rediker Software](https://github.com/Rediker-Software)의 [Django OAuth2 Consumer](https://github.com/Rediker-Software/doac) 라이브러리는 [REST 프레임 워크에 대한 OAuth 2.0 지원](https://github.com/Rediker-Software/doac/blob/master/docs/integrations.md#)을 제공하는 또 다른 패키지입니다. 이 패키지에는 토큰에 대한 토큰 범위 지정 권한이 포함되어있어 API에 대한 세밀한 액세스가 가능합니다.

### JSON Web Token 
JSON Web Token은 토큰 기반 인증에 사용할 수있는 상당히 새로운 표준입니다. 내장 된 TokenAuthentication 체계와 달리 JWT 인증은 데이터베이스를 사용하여 토큰의 유효성을 검사 할 필요가 없습니다. [Blimp](https://github.com/GetBlimp)는 JWT 인증 클래스를 제공하는 [djangorestframework-jwt](https://github.com/GetBlimp/django-rest-framework-jwt) 패키지와 클라이언트가 사용자 이름과 비밀번호가 있는 JWT를 얻을 수 있는 메커니즘을 유지합니다.

### Hawk HTTP Authentication
[HawkREST](https://hawkrest.readthedocs.io/en/latest/) 라이브러리는 [Mohawk](https://mohawk.readthedocs.io/en/latest/) 라이브러리를 기반으로 [Hawk](https://github.com/hueniverse/hawk)에서 서명 한 요청 및 응답을 API에서 사용할 수 있도록합니다. [Hawk](https://github.com/hueniverse/hawk)은 공유 키로 서명 된 메시지를 사용하여 두 당사자가 서로 안전하게 통신 할 수있게합니다. [HTTP MAC 액세스 인증](https://tools.ietf.org/html/draft-hammer-oauth-v2-mac-token-05) ([OAuth 1.0](https://oauth.net/core/1.0a/)의 일부를 기반으로 함)을 기반으로합니다.

### HTTP Signature 
HTTP 서명 (현재 [IETF 초안](https://datatracker.ietf.org/doc/draft-cavage-http-signatures/))은 HTTP 메시지에 대한 원본 인증 및 메시지 무결성을 달성하는 방법을 제공합니다. 많은 서비스에서 사용되는 [Amazon의 HTTP 서명 체계](http://docs.aws.amazon.com/general/latest/gr/signature-version-4.html)와 유사하게 상태 비 저장 요청 별 인증을 허용합니다. [Elvio Toccalino](https://github.com/etoccalino/)는 사용하기 쉬운 HTTP 서명 인증 메커니즘을 제공하는 [djangorestframework-httpsignature](https://github.com/etoccalino/django-rest-framework-httpsignature) 패키지를 유지 관리합니다.

### Djoser
[Djoser](https://github.com/sunscrapers/djoser) 라이브러리는 등록, 로그인, 로그 아웃, 비밀번호 재설정 및 계정 활성화와 같은 기본 작업을 처리하기 위한 일련의 보기를 제공합니다. 패키지는 custom 사용자 모델과 작동하며 토큰 기반 인증을 사용합니다. 이것은 Django 인증 시스템의 REST 구현을 사용할 준비가되었습니다.

### django-rest-auth
[Django-rest-auth](https://github.com/Tivix/django-rest-auth) 라이브러리는 등록, 인증 (소셜 미디어 인증 포함), 비밀번호 재설정, 사용자 세부 정보 검색 및 업데이트 등을 위한 일련의 REST API 엔드포인트를 제공합니다. 이러한 API 엔드포인트를 사용하면 AngularJS, iOS, Android 및 기타 사용자는 사용자 관리를 위해 REST API를 통해 독립적으로 Django 백엔드 사이트와 통신 할 수 있습니다.

### django-rest-framework-social-oauth2
[Django-rest-framework-social-oauth2](https://github.com/PhilipGarnero/django-rest-framework-social-oauth2) 라이브러리는 소셜 플러그인 (facebook, twitter, google 등)을 인증 시스템에 쉽게 통합하고 쉬운 oauth2 설정을 제공합니다. 이 라이브러리를 사용하면 외부 토큰 (예 : 페이스 북 액세스 토큰)을 기반으로 사용자를 인증하고 이러한 토큰을 "in-house" oauth2 토큰으로 변환하고 oauth2 토큰을 사용 및 생성하여 사용자를 인증 할 수 있습니다.

### django-rest-knox
[Django-rest-knox](https://github.com/James1345/django-rest-knox) 라이브러리는 단일 페이지 응용 프로그램 및 모바일 클라이언트를 염두에 두고 기본 TokenAuthentication 체계보다 안전하고 확장 가능한 방식으로 토큰 기반 인증을 처리 할 수 있는 모델과 뷰를 제공합니다. 클라이언트 별 토큰 및 일부 다른 인증 (일반적으로 기본 인증)이 제공된 경우 생성하는 View, 토큰을 삭제 (서버 강제 로그 아웃 제공) 및 모든 토큰 삭제(사용자가 로그인 한 모든 클라이언트 로그 아웃) view를 제공합니다.).

---

## 추가 내용 (Token 등록 및 삭제)

**`member_myuser`**
![](./images/token1.png)
**`authtoken_token`**
![](./images/token2.png)
**`postman`에서 토큰 생성**
![](./images/token3.png)

`token`의 `user_id` 값은 `member_myuser`의 `id` 값으로 등록됩니다.  
postman에서 생성한 test5(username)의 `myuser`테이블에서의 id 값은 8이고, 해당 토큰값으로 `token`테이블을 비교해보면 `user_id`가 같은 것을 확인할 수 있습니다.  

`token` 삭제는 해당 토큰값의 계정으로 로그인해야 삭제가 가능합니다.

![](./images/token_delete.png)
> `request.user`를 프린트해보면 `username`값이 조회됩니다.
