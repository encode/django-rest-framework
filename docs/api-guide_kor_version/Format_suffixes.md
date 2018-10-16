# Django REST Framework - Format suffixes

---

_"Section 6.2.1 does not say that content negotiation should be used all the time."_  


_"섹션 6.2.1은 content negotiation이 항상 사용되어야한다고 말하지 않는다. "_  

_— Roy Fielding, REST discuss mailing list_

---

## Format suffixes
웹 API의 일반적인 패턴은 URL에서 파일 이름 확장자를 사용하여 특정 미디어 유형에 대한 엔드포인트를 제공하는 것입니다. 예를 들어, 'http://example.com/api/users.json'은 JSON 표현을 제공합니다.  
API의 URLconf에 있는 각 개별 항목에 형식 접미사 패턴을 추가하는 것은 오류가 발생하기 쉽고 DRY가 아니므로 REST 프레임워크는 이러한 패턴을 URLconf에 추가하는 방법을 제공합니다.

### format_suffix_patterns
**Signature**: format_suffix_patterns(urlpatterns, suffix_required=False, allowed=None)  

제공된 각 URL 패턴에 추가 된 형식 접미사 패턴을 포함하는 URL 패턴 list를 반환합니다.  

Arguments:  

- `urlpatterns` : **필수**. URL 패턴 목록.
- `suffix_required` : 선택사항. URL의 접미사를 옵션으로 하는지, 필수로 하는지를 나타내는 boolean입니다. 디폴트는 `False`입니다. 접미사는 기본적으로 선택사항입니다.
- `allowed` : 선택사항. 유효한 형식 접미사의 list 또는 tuple입니다. 제공되지 않으면 와일드 카드 형식 접미사 패턴이 사용됩니다.

예:

```python
from rest_framework.urlpatterns import format_suffix_patterns
from blog import views

urlpatterns = [
    url(r'^/$', views.apt_root),
    url(r'^comments/$', views.comment_list),
    url(r'^comments/(?P<pk>[0-9]+)/$', views.comment_detail)
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'html'])
```
`format_suffix_patterns`를 사용하는 경우 `'format'`키워드 인수를 해당 부에 추가해야합니다. 예:

```python
@api_view(('GET', 'POST'))
def comment_list(request, format=None):
    # do stuff...
```
또는 class-bassed-views:

```python
class CommentList(APIView):
    def get(self, request, format=None):
        # do stuff...

    def post(self, request, format=None):
        # do stuff...
```
사용 된 kwarg의 이름은 `FORMAT_SUFFIX_KWARG`설정을 사용하여 수정할 수 있습니다.  
또한 `format_suffix_patterns`는 `include`URL 패턴으로 내림차순을 지원하지 않습니다.  

#### Using with `i18n_patterns`
Django에서 제공하는 `i18n_patterns`함수와 `format_suffix_patterns`를 사용하는 경우 `i18n_patterns` 함수가 최종 함수 또는 가장 바깥쪽 함수로 적용되는지 확인해야합니다. 예:

```python
url patterns = [
    …
]

urlpatterns = i18n_patterns(
    format_suffix_patterns(urlpatterns, allowed=['json', 'html'])
)
```

---

### Query parameter formats
format suffixe의 대신 요청 된 쿼리 parameter에 포함시키는 것입니다. REST 프레임워크는 기본적으로 옵션을 제공하며, browsable API에서 사용 가능한 다양한 표현을 전환하는데 사용됩니다.  
짧은 형식을 사용하여 표현을 선택하려면 `format` 쿼리 parameter를 사용하십시오. 예 : `http://example.com/organizations/?format=csv`  
이 쿼리 parameter의 이름은 `URL_FORMAT_OVERRIDE`설정을 사용하여 수정할 수 있습니다. 이 동작을 사용하지 않으려면 값을 `None`으로 설정하세요.

### Accept headers vs. format suffixes
파일 이름 확장자는 RESTfull 패턴이 아니면 HTTP Accept 헤더가 항상 대신 사용되어야 한다는 웹 커뮤니티의 견해가 있는 것 같습니다.  
그것은 실제론 오해입니다. 예를 들어 Roy Fileding은 쿼리 parameter 미디어 타입 표시기와 파일 확장 미디어 타입 표시기의 상대적 장점에 대해 다음과 같이 설명합니다.  
_"그래서 나는 항상 확장 프로그램을 선호합니다. 어느 선택도 REST와는 아무런 관련이 없습니다. "- Roy Fielding, REST 토론 메일 링리스트_  

인용문에는 Accept Headers가 언급되어 있지 않지만 format suffix는 허용되는 패턴으로 간주되어야 한다는 점을 분명히 합니다.