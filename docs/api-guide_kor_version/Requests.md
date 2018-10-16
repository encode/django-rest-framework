# Django REST Framework - Requests

---
_"If you're doing REST-based web service stuff ... you should ignore request.POST."   
"REST 기반 웹 서비스 작업을 하고있다면 ... POST 요청을 무시해야한다."  
— Malcom Tredinnick_


## Requests

REST 프레임워크의 `Request` 클래스는 표준 `HttpRequest`를 확장하여 REST 프레임워크의 유연한 request 구문 분석 및 요청 인증을 지원합니다.

## Request parsing
REST 프레임워크의 Request 객체는 유연한 request 구문 분석 기능을 제공하므로 사용자가 일반적으로 form 데이터를 처리하는 것과 같은 방식으로 JSON 데이터 또는 다른 미디어 유형으로 요청을 처리 할 수 ​​있습니다.

### .data
`request.data`는 요청 본문의 구문 분석 된 내용을 반환합니다. 이는 다음을 제외하고 표준 `request.POST` 및 `request.FILES` 속성과 유사합니다.

- 여기에는 파일과 파일이 아닌 입력을 포함하여 파싱 된 모든 내용이 포함됩니다.
- `POST`가 아닌 `HTTP`메소드의 컨텐츠 분석을 지원합니다. 즉, `PUT`과 `PATCH` 요청의 컨텐츠에 액서스 할 수 있습니다.
- 이는 form 테이터를 지원하는 것보다 REST 프레임워크의 유연한 request 구문 분석을 지원합니다. 예를 들어, 들어오는 form 데이터를 처리하는 것과 같은 방식으로 들어오는 JSON 데이터를 처리 할 수 있습니다.
더 자세한 내용은 [parsers documentation](http://www.django-rest-framework.org/api-guide/parsers/)을 참조하세요.

### .query_params
`request.query_params`는 `request.GET`에 대해 보다 정확하게 명명 된 동의어입니다.  
코드 내에서 명확성을 위해 Django의 표준 `request.GET` 대신 `request.query_params`를 사용하는 것이 좋습니다. 이렇게 하면  코드베이스를 보다 정확하고 명확하게 유지할  수 있습니다. 모든 HTTP 메소드 유형에는 `GET`request 뿐만 아니라 쿼리 parameter가 포함될 수 있습니다.

### .parsers
`APIView` 클래스나 `@api_view` 데코레이터는 뷰에 설정 된 `parser_classes`나 `DEFAULT_PARSER_CLASSES`설정에 따라 속성이 자동으로 `Parser` 인스턴스 목록으로 설정되도록 합니다.  
일반적으로 이 속성에 액서스 할 필요는 없습니다.

---
**NOTE**: 클라이언트가 조작 된 콘텐츠를 보낸 경우 `request.data`에 액서스하면  `ParserError`가 발생할 수 있습니다. 기본적으로 REST 프레임워크의 `APIView` 클래스나 `@api_view`데코레이터는 오류를 포착하고, `400 Bad Request` 응답을 반환합니다.  
클라이언트가 파싱 할 수 없는 content-type을 가진 request를 보내면 `UnsuppoertedMediaType`예외가 발생합니다. 이 예외는 기본적으로 포착되어 지원되지 않는 미디어 유형 응답을 반환합니다.

---

## Content negotiation
request는 콘텐츠 협상 단계의 결과를 결정할 수 있는 몇가지 속성을 제공합니다. 이를 통해 다양한 미디어 유형에 대해 다른 serializer 스키마를 선택하는 것과 같은 동작을 구현할 수 있습니다.

### .accepted_renderer
renderer 인스턴스는 컨텐츠 협상 단계에서 선택 된 인스턴스입니다.

### .accepted_media_type
내용 협상 단계에서 수락 한 미디어 유형을 나타내는 문자열입니다.

---

## Authentication (입증)
REST 프레임워크는 다음과 같은 기능을 제공하는 유연한 request 별 인증을 제공합니다.

- API의 다른 부분에 대해 서로 다른 인증 정책을 사용합니다.
- 다중 인증 정책의 사용을 지원합니다.
- 들어오는 request와 관련된 사용자와 토큰 정보를 제공합니다.

### .user
`request.user`는 일반적으로 `django.contrib.auth.models.User`의 인스턴스를 반환하지만 동작은 사용되는 인증 정책에 따라 다릅니다.  
request이 인증되지 않은 경우 request.user의 기본값은 `django.contrib.auth.models.AnonymousUser`의 인스턴스입니다.
자세한 내용은 [authentication documentation](http://www.django-rest-framework.org/api-guide/authentication/)을 참조하세요.

### .auth
`request.auth`는 추가 인증 컨텍스트를 리턴합니다. `request.auth`의 정확한 작동은 사용되는 인증 정책에 따라 다르지만 대개 request가 인증 된 토큰의 인스턴스 일 수 있습니다.  
request가 인증되지 않았거나 추가 컨텍스트가 없는 경우, `request.auth`의 기본값은 없습니다.  
자세한 내용은 [authentication documentation](http://www.django-rest-framework.org/api-guide/authentication/)을 참조하세요.

### .authenticators
`APIView` 클래스나 `@api_view`데코레이터는 뷰에 설정된 `authentication_classes`나 `DEFAULT_AUTHENTICATORS` 설정에 따라 속성이 자동으로 `Authentication`인스턴스 목록으로 설정되도록 합니다.  
일반적으로 이 속성에 액서스 할 필요는 없습니다.

---

## Browser enhancements
REST 프레임워크는 브라우저 기반의 `PUT`, `PATCH`, `DELETE` form과 같은 몇 가지 브라우저 개선 사항을 지원합니다.

### .method
`request.method`는 request의 HTTP 메소드의 **uppercased**(대문자)로 된 문자열 표현을 리턴합니다.  
브라우저 기반의 `PUT`, `PATCH` 및 `DELETE` form이 투명하게 지원됩니다.  
자세한 내용은 [browser enhancements documentation](http://www.django-rest-framework.org/topics/browser-enhancements/)을 참조하세요.

### .content_type
`request.content_type`은 HTTP request 본문의 미디어 유형을 나타내는 문자열 객체를 반환하거나 미디어 유형이 제공되지 않은 경우 빈 문자열을 반환합니다.  
일반적으로 REST 프레임워크의 기본 request 구문 분석 동작에 의존하므로 일반적으로 request의 콘텐츠 형식에 직접 액서스 할 필요가 없습니다.  
request의 콘텐츠 형식에 액서스해야하는 경우 브라우저 기반 non-form 콘텐츠에 대한 투명한 지원을 제공하므로 `request.META.get('HTTP_CONTENT_TYPE')`을 사용하는 것보다 `.content_type`속성을 사용해야 합니다.  
자세한 내용은 [browser enhancements documentation](http://www.django-rest-framework.org/topics/browser-enhancements/)을 참조하세요.

### .stream
`request.stream`은 request 본문의 내용을 나타내는 스트림을 반환합니다.  
일반적으로 REST 프레임워크의 기본 request 구문 분석 동작에 의존하므로 대개 request의 콘텐츠에 직접 액세스 할 필요가 없습니다.

---

## Standard HttpRequest attributes
REST 프레임워크의 `request`는 Django의 `HttpRequest`를 확장하므로 다른 모든 표준 속성과 메소드도 사용할 수 있습니다. 예를 들어, `request.META`와 `request.session` dict는 정상적으로 사용 가능합니다.  
구현 이유로 인해 `Request`클래스는 `HttpRequest`클래스에 상속하지 않고 대신 `composition`을 사용하여 클래스를 확장합니다.
