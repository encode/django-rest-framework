# Django REST framework - Serializer fields

---

_"Each field in a Form class is responsible not only for validating data, but also for "cleaning" it — normalizing it to a consistent format."_  

_"Form 클래스의 각 필드는 데이터 유효성 검사뿐만 아니라 일관된 형식으로 정규화하려 "정리"하는 역할을 담당합니다."_  

_— Django documentation_  

---

## Serializer fields
serializer 필드는 기존 값과 내부 데이터 유형간의 변환을 처리합니다. 또한 입력 값의 유효성 검사와 부모 오브젝트에서 값 검색 및 설정을 처리합니다.

---

**Note**: serializer 필드는 `fields.py`에 선언되어 있지만, 규칙에 따라 `from rest)framework import serializer`에서 가져와서 `setializers.<FiledName>` 필드를 참조해야합니다.

---

### Core arguments
각 serializer 필드 생성자는 최소한 이러한 인수를 취합니다. 일부 Field 클래스는 필드 별 인수를 추가로 가져오지만 항상 다음 사항을 받아들여야합니다.  

`read_only`  
읽기 전용 필드는  API 출력에 포함되지만 create 또는 update 조작 중 입력에 포함되면 안됩니다. serializer 입력에 잘못 된 'read_only'필드는 무시됩니다.  
표현식을 serializer 할 떄 필드가 사용되도록하려면 이 값을 `True`로 설정하고 serializer 복원 중 인스턴스를 만들거나 업데이트 할 떄는 필드를 사용하지 마세요.

Default: `False`  

`write_only`  
이 값을 `True`로 설정하면 인스턴스를 업데이트하거나 만들때 필드가 사용될 수 있지만 표현을 serializer 할 때는 필드가 포함되지 않습니다.  

Default: `True`  

`required`  
deserializer 중에 필드가 제공되지 않으면 일반적으로 오류가 발생합니다. deserializer 중에 이 필드가 필요하지 않은 경우 `False`로 설정하세요.  
이 값을 `False`로 설정하면 인스턴스를 serializer 할 때 객체 속성 또는 dict 키가 출력에 생략 될 수 있습니다. 키가 없으면 출력 표현에 포함되지 않습니다.  

Default: `True`  

`allow_null`  
serializer 필드에 `None`이 전달되면 일반적으로 오류가 발생합니다. `None`을 유효한 값으로 간주해야하는 경우 이 키워드 인수를 `True`로 설정하세요.  

Default: `False`  

`default`  
설정되면, 입력 값이 제공되지 않으면 필드에 사용될 기본값이 제공됩니다. 설정되지 않은 경우 기본 동작은 속성을 전혀 채우지 않는 것입니다.  
부분 업데이트 조작중에는 `default`값이 적용되지 않습니다. 부분 업데이트의 경우 들어오는 데이터에서 제공되는 필드에만 유효성 검사 된 값이 반환됩니다.  
함수 또는 다른 호출 가능 객체로 설정 될 수 있습니다. 이 경우 값은 사용될 때마다 평가됩니다. 호출 될 때 인수가 없습니다. 'callable'에 `set_context`메서드가 있는 경우, 필드 인스턴스를 인수로 사용하기 전에 매번 호출됩니다. 이는 [validators](http://www.django-rest-framework.org/api-guide/validators/#using-set_context)와 동일한 방식으로 작동합니다.  
인스턴스를 serializer 할 때 오브젝트 속성 또는 dict 키가 인스턴스에 없는 경우 기본값이 사용됩니다.  
기본값을 설정하면 필드가 필요하지 않음을 의미합니다. 기본 및 필수 키워드 인수를 모두 포함하면 올바르지 않으며 오류가 발생합니다.  

`source`  
필드를 채우는데 사용할 속성의 이름입니다. `URLField(source='get_absolute_url')`와 같은 자체 인수만 사용하거나 `EmailField(source='user.email')`와 같은 속성을 통과하는 점으로 구분 된 표기법을 사용할 수 있습니다.  
값 `source='*'`는 특별한 의미를 가지며 전체 객체가 필드로 전달되어야 함을 나타내기 위해 사용됩니다. 중첩된 표현을 작성하거나 출력 표현을 결정하기 위해 전체 오브젝트에 액세스해야하는 필드에 유용합니다.  
기본값은 필드의 이름입니다.  

`validators`  
입력 필드 입력에 적용되어야하고 유효성 검사 오류를 발생시키거나 단순히 반환해야하는 validator 함수의 list입니다. 'Validator'함수는 일반적으로 `serializers.ValidationError`를 발생시켜야하지만 Django에 내장된 `ValidationError`는 Djang 코드베이스 또는 타사 Django 패키지에 정의된 유효성 검사기와의 호환성을 위해 지원됩니다.  

`error_messages`  
오류 메시지에 대한 오류코드 dict  

`label`  
HTML 양식 필드 또는 기타 설명적인 요소의 필드 이름으로 사용할 수 있는 짧은 텍스트 문자열입니다.  

`help_text`  
HTML 양식 필드나 기타 설명적인 요소의 필드에 대한 설명으로 사용될 수 있는 텍스트 문자열입니다.  

`initial`  
HTML 양식 피드 값을 미리 채우는 데 사용해야하는 값입니다. 일반 Django `field`와 마찬가지로 호출 대상을 전달할 수 있습니다.  

```python
import datetime
from rest_framework import serializers
class ExampleSerializer(serializers.Serializer):
    day = serializers.DateField(initial=datetime.date.today)
```

`style`  
렌더러가 필드를 렌더링하는 방법을 제어하는데 사용할 수 있는 key-value dict입니다.  
다음은 `'input_type'`과 `'base_template'`의 두 가지 예입니다.

```python
# Use <input type="password"> for the input.
password = serializers.CharField(
    style={'input_type': 'password'}
)

# Use a radio input instead of a select input.
color_channel = serializers.ChoiceField(
    choices=['red', 'green', 'blue'],
    style={'base_template': 'radio.html'}
)
```
자세한 내용은  [HTML & Forms documentation](http://www.django-rest-framework.org/topics/html-and-forms/)를 참조하세요.

---

## Boolean fields

### BooleanField
boolean 표현입니다.  

HTML으로 인코딩 된 양식 입력을 사용할 때 `default=True`옵션이 지정되어 있어도 값을 생략하면 항상 필드를 `False`로 설정하는 것으로 처리됩니다. 이것은 HTML 체크 상자 입력이 값을 생략하여 선택되지 않은 상태를 나타내므로, REST 프레임워크는 생략을 빈 체크 박스 입력으로 처리합니다.  
`django.db.models.fields.BooleanField`에 해당합니다.  

**Signature**: `BooleanField()`  

### NullBooleanField
유효한 값으로 `None`도 허용하는 boolean 표현입니다.  
`django.db.models.fields.NullBooleanField`에 해당합니다.  

**Signature**: `NullBooleanField()`

---

## String fields

### CharField
텍스트 표현입니다. 선택적으로 텍스트가 `max_length`보다 짧고 `min_length`보다 길도록 유효성을 검사합니다.  
`django.db.models.fields.CharField` 또는 `django.db.models.fields.TextField`에 해당합니다.  

**Signature**: `CharField(max_length=None, min_length=None, allow_blank=False, trim_whitespace=True)`

- `max_length` : 입력이 이 문자 수를 초과하지 않는지 확인합니다.
- `min_length` : 입력에 이 수보다 적은 문자가 들어 있는지 확인합니다.
- `allow_blank` : `True`로 설정하면 빈 문자열을 유효한 값으로 간주해야합니다. `False`로 설정하면 빈 문자열이 유효하지 않은 것으로 간주되어 유효성 검사 오류가 발생합니다. 기본값은 `False`입니다.
- `rim_whitespace` : `True`로 설정하면 앞뒤 공백이 잘립니다. 기본값은 `True`입니다.

`allow_null` 옵션은 문자열 필드에도 사용할 수 있지만, `allow_blank`를 사용하면 사용하지 않는 것이 좋습니다. `allow_blank=True`와 `allow_null=True`를 모두 설정하는 것은 유효하지만 문자열 표현에 허용되는 두 가지 유형의 빈 값이 존재하므로 데이터 불일치와 미세한 응용 프로그램 버그가 발생할 수 있습니다.

### EmailField
텍스트 표현은 유효한 Email 주소로 텍스트의 유효성을 검사합니다.  
`django.db.models.fields.EmailField`에 해당합니다.  

**Signature**: `EmailField(max_length=None, min_length=None, allow_blank=False)`

### RegexField
지정된 값의 유효성을 검사하는 텍스트 표현은 특정 정규 표현식과 일치합니다.  
`django.forms.fields.RegexField`에 해당합니다.  

**Signature**: `RegexField(regex, max_length=None, min_length=None, allow_blank=False)`  

필수 정규 표현식 인자는 문자열이거나 컴파일 된 파이썬 정규 표현식 객체일 수 있습니다.  
검증을 위한 Django의 `django.core.validators.RegexValidator`을 사용합니다.

### SlugField
패턴 `[a-zA-Z0-9_-]+`에 대한 입력의 유효성을 검사하는 `RegexField`입니다.  
`django.db.models.fields.SlugField`에 해당합니다.  

**Signature**: `SlugField(max_length=50, min_length=None, allow_blank=False)`

### URLField
URL 일치 패턴에 대해 입력의 유효성을 검사하는 `RegexField`입니다. `http://<host>/<path>` 형식의 정규화 된 URL이 필요합니다.  
`django.db.models.fields.URLField`에 해당합니다. 확인을 위해 장고의 `django.core.validators.URLValidator`을 사용합니다.  

**Signature**: `URLField(max_length=200, min_length=None, allow_blank=False)`

### UUIDField
입력이 유효한 UUID 문자열임을 보장하는 필드입니다. `to_internal_value` 메서드는 `uuid.UUID` 인스턴스를 리턴합니다. 출력시 필드는 정규 하이픈 형시의 문자열을 반환합니다. 예:

```
"de305d54-75b4-431b-adb2-eb6b9e546013"
```
**Signature**: `UUIDField(format='hex_verbose')`

- `format` : uuid 값의 표현 형식을 결정합니다.
	- `'hex_verbose'` : 하이픈을 포함한 비표준 16 진수 표현 : `"5ce0e9a5-5ffa-654b-cee0-1238041fb31a"`
	- `'hex'` : 하이픈을 제외하고 UUID의 압축 된 16 진수 표현 : `"5ce0e9a55ffa654bcee01238041fb31a"`
	- `'int'` : UUID의 128 비트 정수 표현 : `"123456789012312313134124512351145145114"`
	- `'urn'` : RFC 4122 URID의 URN 표현 : `"urn:uuid:5ce0e9a5-5ffa-654b-cee0-1238041fb31a"`형식 parameter를 변경하면 표현 값에만 영향을 줍니다. 모든 형식은 `to_internal_value`에서 허용됩니다.

### FilePathField
파일 시스템의 특정 디렉토리에 있는 파일 이름으로 제한 되는 필드입니다.  
`django.forms.fields.FilePathField`에 해당합니다.  

**Signature**: `FilePathField(path, match=None, recursive=False, allow_files=True, allow_folders=False, required=None, **kwargs)`  

- `path` : 이 FilePathField가 선택해야하는 디렉토리에 대한 절대 파일 시스템 경로.
- `match` : 파일 경로 필터링을 사용하여 파일 이름을 필터링하는 정규 표현식입니다.
- `recursive` : path의 모든 하위 디렉토리가 포함되어야하는지 여부를 지정합니다. 기본값은 `False`입니다.
- `allow_files` : 지정된 위치의 파일을 포함할지 여부를 지정합니다. 기본값은 `True`입니다. `allow_files` 또는 `allow_folders`는 `True` 이어야합니다.  
- `allow_folders` : 지정된 위치의 폴더를 포함할지 여부를 지정합니다. 기본값은 `False`입니다. `allow_folders` 또는 `allow_files`는 `True` 여야합니다.

### IPAddressField
입력이 유효한 IPv4 또는 IPv6 문자열인지 확인하는 필드입니다.  
`django.forms.fields.IPAddressField`와 `django.forms.fields.GenericIPAddressField`에 해당합니다.  

**Signature**: `IPAddressField(protocol='both', unpack_ipv4=False, **options)`  

- `protocol`의 유효한 입력을 지정된 프로토콜로 제한합니다. 허용되는 값은 'both'(기본값), 'IPv4'또는 'IPv6'입니다. 매칭은 대소문자를 구분하지 않습니다.
- `unpack_ipv4`은 `::ffff:192.0.2.1`과 같은 IPv4 매핑 주소의 압축을 풉니다. 이 옵션을 사용하면 주소가 `192.0.2.1`로 압축 해제됩니다. 기본값은 사용하지 않습니다. 프로토콜이 'both'로 설정된 경우에만 사용할 수 있습니다.

---

## Numeric fields

### IntegerField
정수 표현.  

`django.db.models.fields.IntegerField`, `django.db.models.fields.SmallIntegerField`, `django.db.models.fields.PositiveIntegerField`, `django.db.models.fields.PositiveSmallIntegerField`에 해당합니다.  

**Signature**: `IntegerField(max_value=None, min_value=None)`  

- `max_value` : 제공된 숫자가이 값보다 크지 않은지 확인합니다.
- `min_value` : 제공된 숫자가이 값보다 작지 않음을 검증합니다.  

### FloatField
부동 소수점 표현.  

`django.db.models.fields.FloatField`에 해당합니다.  

**Signature**: `FloatField(max_value=None, min_value=None)`

- `max_value` : 제공된 숫자가이 값보다 크지 않은지 확인합니다.
- `min_value` : 제공된 숫자가이 값보다 작지 않음을 검증합니다. 

### DecimalField
10 진수 표현으로, Python에서 `Decimal` 인스턴스로 나타냅니다.  

`django.db.models.fields.DecimalField`에 해당합니다.  

**Signature**: `DecimalField(max_digits, decimal_places, coerce_to_string=None, max_value=None, min_value=None)`

- `max_digits` : 숫자에 허용되는 최대 자릿수. `None`이거나 `decimal_places`보다 크거나 같은 정수 여야합니다.
- `decimal_places` : 숫자와 함께 저장할 소수 자릿수입니다.
- `coerce_to_string` : 표현식에 문자열 값을 반환해야하는 경우 `True`로 설정하고 `Decimal` 객체를 반환해야하는 경우 `False`로 설정합니다. 기본값은 `COERCE_DECIMAL_TO_STRING` 설정 키와 같은 값으로, 오버라이드 하지 않으면 `True`입니다. serializer가 `Decimal` 객체를 반환하면 최종 출력 형식은 렌더러에 의해 결정됩니다. `localize`를 설정하면 값이 `True`로 설정됩니다.
- `max_value` : 제공된 숫자가이 값보다 크지 않은지 확인합니다.
- `min_value` : 제공된 숫자가이 값보다 작지 않음을 검증합니다. 
- `localize` : 현재 로케일을 기반으로 입력 및 출력의 지역화를 사용하려면 `True`로 설정하십시오. 또한 `coerce_to_string`을 `True`로 설정합니다. 기본값은 `False`입니다. 설정 파일에서 `USE_L10N=True`로 설정하면 데이터 서식이 활성화됩니다.

#### Example usage
소수점 2 자리의 해상도로 999까지의 숫자의 유효성을 검사하려면 다음을 사용합니다.

```
serializers.DecimalField(max_digits=5, decimal_places=2)
```
소수 자릿수 10의 해상도로 10 억 미만의 숫자를 검증하려면 다음을 수행하십시오.

```
serializers.DecimalField(max_digits=19, decimal_places=10)
```
이 필드에는 선택적 인수 `coerce_to_string`도 사용됩니다. `True`로 설정하면 표현이 문자열로 출력됩니다. `False`로 설정하면 표현은 `Decimal`인스턴스로 남게되고 최종 표현은 렌더러에 의해 결정됩니다.  
설정을 해제하면 기본값은 `COERCE_DECIMAL_TO_STRING`설정과 동일한 값으로 설정되며, 그렇지 않은 경우 `True`로 설정됩니다.

---

## Date and time fields

### DateTimeField
날짜 및 시간 표현.  

`django.db.models.fields.DateTimeField`에 해당합니다.  

**Signature**: `DateTimeField(format=api_settings.DATETIME_FORMAT, input_formats=None)`  

- `format` : 출력 포맷을 나타내는 문자열. 지정하지 않으면 기본값은 `DATETIME_FORMAT` 설정 키와 동일한 값으로 설정되며, 설정하지 않으면 `'iso-8601'`이 됩니다. 형식 문자열로 설정하면 `to_representation` 반환 값을 문자열 출력으로 강제 변환해야합니다. 형식 문자열은 아래에 설명되어 있습니다. 이 값을 `None`으로 설정하면 Python `datetime` 객체가 `to_representation`에 의해 반환되어야합니다. 이 경우 datetime 인코딩은 렌더러에 의해 결정됩니다.
- `input_formats` : 날짜를 파싱하는데 사용할 수 있는 입력 형식을 나타내는 문자열 list입니다. 지정하지 않으면 `DATETIME_INPUT_FORMATS` 설정이 사용되며 기본값은 `['iso-8601']`입니다.

#### `DateTimeField` format strings.
형식 문자열은 명시적으로 형식을 지정하는 [Python `strftime`](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) 형식이거나 [ISO 8601](https://www.w3.org/TR/NOTE-datetime) 스타일 datetimes가 사용되어야 함을 나타내는 특수 문자열 `'iso-8601'`일 수 있습니다. (예 : `'2013-01-29T12:34:56.000000Z'`)  
형식의 값으로 `None` 값이 사용되면 `datetime` 객체는 `to_representation`에 의해 반환되고 최종 출력 표현은 렌더러 클래스에 의해 결정됩니다.  

#### `auto_now` and `auto_now_add` model fields
`ModelSerializer` 또는 `HyperlinkedModelSerializer`를 사용할 때 `auto_now=True` 또는 `auto_now_add=True` 인 모델 필드는 기본적으로 `read_only=True` 인 serializer 필드를 사용합니다.  
이 동작을 재정의하려면 serializer에서 `DateTimeField`를 명시적으로 선언해야합니다. 예 :

```python
class CommentSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField()

    class Meta:
        model = Comment
```

### DateField
날짜 표현입니다.  

`django.db.models.fields.DateField`에 해당합니다.  

**Signature**: `DateField(format=api_settings.DATE_FORMAT, input_formats=None)`

- `format` : 출력 포맷을 나타내는 문자열. 지정하지 않으면 기본값은 `DATE_FORMAT` 설정 키와 동일한 값으로 설정되며, 설정하지 않으면 `'iso-8601'`이 됩니다. 형식 문자열로 설정하면 `to_representation` 반환 값을 문자열 출력으로 강제 변환해야합니다. 형식 문자열은 아래에 설명되어 있습니다. 이 값을 `None`으로 설정하면 Python `date` 객체가 `to_representation`에 의해 반환되어야합니다. 이 경우 date 인코딩은 렌더러에 의해 결정됩니다.
- `input_formats` : date를  파싱하는 데 사용할 수 있는 입력 형식을 나타내는 문자열 목록입니다. 지정하지 않으면 `DATE_INPUT_FORMATS` 설정이 사용되며 기본값은 `['iso-8601']`입니다.

#### `DateField` format strings
형식 문자열은 명시적으로 형식을 지정하는 [Python strftime 형식](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)이거나 [ISO 8601](https://www.w3.org/TR/NOTE-datetime) 스타일 날짜를 사용해야한다는 것을 나타내는 특수 문자열 `'iso-8601'`일 수 있습니다. (예 : `'2013-01-29'`)

### TimeField
시간 표현.  

`django.db.models.fields.TimeField`에 해당합니다.  

**Signature**: `TimeField(format=api_settings.TIME_FORMAT, input_formats=None)`  

- `format` : 출력 포맷을 나타내는 문자열. 지정하지 않으면 기본값은 `TIME_FORMAT` 설정 키와 동일한 값으로 설정되며, 설정하지 않으면 `'iso-8601'`이 됩니다. 형식 문자열로 설정하면 `to_representation` 반환 값을 문자열 출력으로 강제 변환해야합니다. 형식 문자열은 아래에 설명되어 있습니다. 이 값을 `None`으로 설정하면 Python `time` 객체가 `to_representation`에 의해 반환되어야 함을 나타냅니다. 이 경우 time 인코딩은 렌더러에 의해 결정됩니다.
- `input_formats` : date를 파싱하는데 사용할 수있는 입력 형식을 나타내는 문자열 list입니다. 지정하지 않으면 `TIME_INPUT_FORMATS` 설정이 사용되며 기본값은 `['iso-8601']`입니다.

#### `TimeField` format strings
형식 문자열은 명시적으로 형식을 지정하는 [Python strftime 형식](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)이거나 [ISO 8601](https://www.w3.org/TR/NOTE-datetime) 스타일 시간이 사용되어야 함을 나타내는 특수 문자열 `'iso-8601'`일 수 있습니다. (예 : `'12:34:56.000000'`)

### DurationField
지속 시간 표현. 

`django.db.models.fields.DurationField`에 해당합니다.  

이 필드의 `validated_data`에는 `datetime.timedelta` 인스턴스가 포함됩니다. 표현은 `'[DD] [HH:[MM:]]ss[.uuuuuu]'` 형식의 문자열입니다.

**Note**: 이 필드는 Django 버전 1.8 이상에서만 사용 가능합니다.  

**Signature**: `DurationField()`

---

## Choice selection fields

### ChoiceField
제한된 choice set에서 값을 허용 할 수 있는 필드입니다.  
`ModelSerializer`가 해당 모델 필드에 `choices=...` 인수가 포함되어 있으면 필드를 자동으로 생성하는데 사용됩니다.  

**Signature**: `ChoiceField(choices)`

- `choices` : 유효한 값의 list 또는 `(key, display_name)` tuple의 list.
- `allow_blank` : `True`로 설정하면 빈 문자열을 유효한 값으로 간주해야합니다. `False`로 설정하면 빈 문자열이 유효하지 않은 것으로 간주되어 유효성 검사 오류가 발생합니다. 기본값은 `False`입니다.
- `html_cutoff` : 설정된 경우 HTML 선택 드롭 다운에 표시 될 최대 선택항목 수입니다. 매우 큰 선택 항목이 있는 자동 생성 된 ChoiceField가 템플릿 렌더링을 방해하지 않도록하기 위해 사용할 수 있습니다. 기본값은 `None`입니다.
- `html_cutoff_text` : 설정된 경우 HTML 선택 드롭 다운에서 최대 항목 수가 잘린 경우 텍스트 표시기가 표시됩니다. 기본값은 `"More than {count} items…"`입니다.

`allow_blank`와 `allow_null`은 모두 `ChoiceField`의 유효한 옵션입니다. 하지만 둘 중 하나만 사용하는 것이 좋습니다. `allow_blank`는 텍스트 선택에 선호되고 `allow_null`은 숫자 또는 기타 텍스트가 아닌 선택에 우선해야합니다.

### MultipleChoiceField
제한 된 선택 항목 set에서 선택된 0, 하나 또는 여러 값 집합을 허용 할 수 있는 필드입니다. 하나의 필수 인수를 취합니다. `to_internal_value`는 선택된 값을 포함하는 세트를 리턴합니다.  

**Signature**: `MultipleChoiceField(choices)`

- `choices` : 유효한 값의 list 또는 `(key, display_name)` tuple의 list입니다.
- `allow_blank` : `True`로 설정하면 빈 문자열을 유효한 값으로 간주해야합니다. `False`로 설정하면 빈 문자열이 유효하지 않은 것으로 간주되어 유효성 검사 오류가 발생합니다. 기본값은 `False`입니다.
- `html_cutoff` : 설정된 경우 HTML 선택 드롭 다운에 표시 될 최대 선택 항목 수입니다. 매우 큰 선택 항목이 있는 자동 생성 된 ChoiceField가 템플릿 렌더링을 방해하지 않도록하기 위해 사용할 수 있습니다. 기본값은 `None`입니다.
- `html_cutoff_text` : 설정된 경우 HTML 선택 드롭 다운에서 최대 항목 수가 잘린 경우 텍스트 표시기가 표시됩니다. 기본값은 `"More than {count} items…"`입니다.

`ChoiceField`와 마찬가지로 `allow_blank` 및 `allow_null` 옵션이 모두 유효하지만 하나만 사용하고 둘 다 사용하지 않는 것이 좋습니다. `allow_blank`는 텍스트 선택에 선호되고 `allow_null`은 숫자 또는 기타 텍스트가 아닌 선택에 우선해야합니다.

---

## File upload fields

### Parsers and file uploads.
`FileField` 및 `ImageField` 클래스는 `MultiPartParser` 또는 `FileUploadParser`에서만 사용하기에 적합합니다. 대부분의 파서, 예를 들어. JSON은 파일 업로드를 지원하지 않습니다. Django의 일반 [FILE_UPLOAD_HANDLERS](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-FILE_UPLOAD_HANDLERS)는 업로드 된 파일을 처리하는 데 사용됩니다.

### FileField
파일 표현.  
Django의 표준 FileField 유효성 검사를 수행합니다.  
`django.forms.fields.FileField`에 해당합니다.  

**Signature**: `FileField(max_length=None, allow_empty_file=False, use_url=UPLOADED_FILES_USE_URL)`

- `max_length` : 파일 이름의 최대 길이를 지정합니다.
- `allow_empty_file` : 빈 파일이 허용 된 경우 지정합니다.
- `use_url` : `True`로 설정하면 URL 문자열 값이 출력 표현에 사용됩니다. `False`로 설정하면 파일 이름 문자열 값이 출력 표현에 사용됩니다. `UPLOADED_FILES_USE_URL` 설정 키의 기본값으로 설정되며, 그렇지 않은 경우 `True`로 설정됩니다.

### ImageField
이미지 표현.  
업로드 된 파일 내용을 알려진 이미지 형식과 일치하는지 확인합니다.  

**Signature**: `ImageField(max_length=None, allow_empty_file=False, use_url=UPLOADED_FILES_USE_URL)`

- `max_length` : 파일 이름의 최대 길이를 지정합니다.
- `allow_empty_file` : 빈 파일이 허용 된 경우 지정합니다.
- `use_url` : `True`로 설정하면 URL 문자열 값이 출력 표현에 사용됩니다. `False`로 설정하면 파일 이름 문자열 값이 출력 표현에 사용됩니다. `UPLOADED_FILES_USE_URL` 설정 키의 기본값으로 설정되며, 그렇지 않은 경우 `True`로 설정됩니다.

---

## Composite fields

### ListField
오브젝트의 list를 검증하는 필드 클래스입니다.  

**Signature**: `ListField(child, min_length=None, max_length=None)`  

- `child` : 리스트 내의 object의 검증에 사용하는 필드 인스턴스입니다. 이 인수가 제공되지 않으면 목록에있는 객체의 유효성이 검사되지 않습니다.
- `min_length` : 목록에이 수보다 적은 요소가 포함되는지 확인합니다.
- `max_length` : 목록에이 개수의 요소만 포함되는지 확인합니다.

예를 들어, 정수 목록을 검증하려면 다음과 같은 것을 사용할 수 있습니다.

```python
scores = serializers.ListField(
   child=serializers.IntegerField(min_value=0, max_value=100)
)
```
또한 `ListField` 클래스는 재사용 가능한 목록 필드 클래스를 작성할 수 있는 선언 스타일을 지원합니다.

```python
class StringListField(serializers.ListField):
    child = serializers.CharField()
```
이제 우리는 custom `StringListField` 클래스를 `child` 인자를 제공 할 필요없이 애플리케이션 전반에 재사용 할 수 있습니다.

### DictField
개체 dict을 확인하는 필드 클래스입니다. `DictField`의 키는 항상 문자열 값으로 간주됩니다.  

**Signature**: `DictField(child)`  

- `child` : dict의 값을 확인하는데 사용해야하는 필드 인스턴스입니다. 이 인수가 제공되지 않으면 매핑의 값이 유효하지 않습니다.

예를 들어 문자열과 문자열의 매핑을 검증하는 필드를 만들려면 다음과 같이 작성합니다.

```python
document = DictField(child=CharField())
```
`ListField`와 마찬가지로 선언 스타일을 사용할 수도 있습니다. 예 :

```python
class DocumentField(DictField):
    child = CharField()
```

### JSONField
들어오는 데이터 구조가 유효한  JSON 프리미티브로 구성되었는지 확인하는 필드 클래스입니다. 대체 바이너리 모드에서는 JSON으로 인코딩 된 바이너리 문자열을 나타내고 유효성을 검사합니다.  

**Signature**: `JSONField(binary)`  

- `binary` : `True`로 설정하면 필드가 프리미티브 데이터 구조가 아닌 JSON 인코딩 된 문자열을 출력하고 유효성을 검사합니다. 기본값은 `False`입니다.

---

## Miscellaneous fields

### ReadOnlyField
수정하지 않고 단순히 필드 값을 반환하는 필드 클래스입니다.  

이 필드는 모델 필드가 아닌 속성과 관련된 필드 이름을 포함 할 때 `ModelSerializer`에서 기본적으로 사용됩니다.  

**Signature**: `ReadOnlyField()`  

예를 들어, `has_expired`가 `Account` 모델의 속성 인 경우 다음 serializer가이를 자동으로 `ReadOnlyField`로 생성합니다.

```python
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'account_name', 'has_expired')
```

### HiddenField
사용자 입력에 따라 값을 사용하지 않고 대신 기본값 또는 호출 가능 값에서 값을 가져오는 필드 클래스입니다.  

**Signature**: `HiddenField()`  

예를 들어, serializer 유효성 검사 데이터의 일부로 항상 현재 시간을 제공하는 필드를 포함 시키려면 다음을 사용합니다.

```python
modified = serializers.HiddenField(default=timezone.now)
```
`HiddenField` 클래스는 사전 정의 된 일부 필드 값을 기반으로 실행해야하는 유효성 검사가 있지만 해당 필드를 모두 최종 사용자에게 공개하지 않으려는 경우에만 필요합니다.  
HiddenField에 대한 추가 예제는 [validators](http://www.django-rest-framework.org/api-guide/validators/) 설명서를 참조하십시오.

### ModelField
임의의 모델 필드에 묶을 수 있는 generic 필드입니다. `ModelField`클래스는 serializer/deserializer 작업을 관련 모델 필드에 위임합니다. 이 필드는 새 custom serializer 필드를 만들지 않고도 custom 모델 필드에 대한 serializer 필드를 만드는데 사용할 수 있습니다.  
이 필드는 `ModelSerializer`에서 custom 모델 필드 클래스에 일치하는데 사용됩니다.  

**Signature**: `ModelField(model_field=<Django ModelField instance>)`  

`ModelField`클래스는 일반적으로 내부 사용을 위한 클래스이지만 필요한 경우 API에서 사용할 수 있습니다. `ModelField`를 올바르게 인스턴스화하려면 인스턴스화 된 모델에 첨부 된 필드를 전달해야합니다. 예: `ModelField(model_field=MyModel()._meta.get_field('custom_field'))`

### SerializerMethodField
이 필드는 읽기 전용 필드입니다. 이 클래스는 첨부 된 serializer 클래스에서 메서드를 호출하여 값을 가져옵니다. 객체의 serializer 된 표현에 모든 종류의 데이터를 추가하는데 사용할 수 있습니다.  

**Signature**: `SerializerMethodField(method_name=None)`  

- `method_name` : 호출되는 serializer의 메서드 이름입니다. 포함되지 않은 경우 기본값은 `get_<field_name>`입니다.

`method_name` 인수로 참조되는 serializer 메서드는 serializer 될 객체인 단일 인수 (`self` 외)를 채택해야합니다. 객체의 serializer 된 표현에 포함되기를 원하는 모든 것을 반환해야합니다. 예:

```python
from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    days_since_joined = serializers.SerializerMethodField()

    class Meta:
        model = User

    def get_days_since_joined(self, obj):
        return (now() - obj.date_joined).days
```

## Custom fields
custom 필드를 만들려면 `Field`를 서브 클래스화한 다음 `.to_representation()` 및 `.to_internal_value()`메서드 중 하나 또는 모두를 오버라이드해야합니다. 이 두 메서드는 초기 데이터 유형과 기본 serializer 가능 데이터 유형간에 변환하는데 사용됩니다. 기본 데이터 유형은 일반적으로 number, string, boolean, `date` / `time` / `datetime` 또는 `None` 중 하나입니다. 그것들은 또한 다른 프리미티브 객체만을 포함하는 객체와 같은 list 또는 dict일 수 있습니다. 사용중인 렌더러에 따라 다른 유형이 지원 될 수 있습니다.  
`.to_representation()`메서드는 초기 데이터 유형을 기존의 serializer 가능 데이터 유형으로 변환하기 위해 호출됩니다.  
`.to_internal_value()`메서드는 기본 데이터 유형을 내부 파이썬 표현으로 복원하기 위해 호출됩니다. 데이터가 유효하지 않은 경우 이 메서드는 `serializers.ValidationError`를 발생시켜야합니다.  
버전 2.x에 있던 `WritableField` 클래스는 더 이상 존재하지 않습니다. 필드가 데이터 입력을 지원하면 `Field`의 하위 클래스를 만들고 `to_internal_value()`를 재정의해야합니다.

### Examples
RGB 색상 값을 나타내는 클래스를 serializer하는 예를 살펴 보겠습니다.

```python
class Color(object):
    """
    A color represented in the RGB colorspace.
    """
    def __init__(self, red, green, blue):
        assert(red >= 0 and green >= 0 and blue >= 0)
        assert(red < 256 and green < 256 and blue < 256)
        self.red, self.green, self.blue = red, green, blue

class ColorField(serializers.Field):
    """
    Color objects are serialized into 'rgb(#, #, #)' notation.
    """
    def to_representation(self, obj):
        return "rgb(%d, %d, %d)" % (obj.red, obj.green, obj.blue)

    def to_internal_value(self, data):
        data = data.strip('rgb(').rstrip(')')
        red, green, blue = [int(col) for col in data.split(',')]
        return Color(red, green, blue)
```
기본적으로 필드 값은 객체의 속성에 매핑으로 처리됩니다. 필드 값에 액서스하고 설정하는 방법을 custom 해야하는 경우 `.get_attribute()` 및 `/` 또는 `.get_value()`를 오버라이드해야합니다.  
예를 들어, serializer 되는 객체의 클래스 이름을 나타내는데 사용할 수 있는 필드를 만듭니다.

```python
class ClassNameField(serializers.Field):
    def get_attribute(self, obj):
        # We pass the object instance onto `to_representation`,
        # not just the field attribute.
        return obj

    def to_representation(self, obj):
        """
        Serialize the object's class name.
        """
        return obj.__class__.__name__
```

#### Raising validation errors
위의 `ColorField` 클래스는 현재 데이터 유효성 검사를 수행하지 않습니다. 잘못된 데이터를 나타내려면 `serializers.ValidationError`를 발생시켜야합니다.

```python
def to_internal_value(self, data):
    if not isinstance(data, six.text_type):
        msg = 'Incorrect type. Expected a string, but got %s'
        raise ValidationError(msg % type(data).__name__)

    if not re.match(r'^rgb\([0-9]+,[0-9]+,[0-9]+\)$', data):
        raise ValidationError('Incorrect format. Expected `rgb(#,#,#)`.')

    data = data.strip('rgb(').rstrip(')')
    red, green, blue = [int(col) for col in data.split(',')]

    if any([col > 255 or col < 0 for col in (red, green, blue)]):
        raise ValidationError('Value out of range. Must be between 0 and 255.')

    return Color(red, green, blue)
```
`.fail()`메서드는 `error_messages` dict에서 메시지 문자열을 취하는 `ValidationError`를 발생시키는 shortcut 입니다. 예:

```python
default_error_messages = {
    'incorrect_type': 'Incorrect type. Expected a string, but got {input_type}',
    'incorrect_format': 'Incorrect format. Expected `rgb(#,#,#)`.',
    'out_of_range': 'Value out of range. Must be between 0 and 255.'
}

def to_internal_value(self, data):
    if not isinstance(data, six.text_type):
        self.fail('incorrect_type', input_type=type(data).__name__)

    if not re.match(r'^rgb\([0-9]+,[0-9]+,[0-9]+\)$', data):
        self.fail('incorrect_format')

    data = data.strip('rgb(').rstrip(')')
    red, green, blue = [int(col) for col in data.split(',')]

    if any([col > 255 or col < 0 for col in (red, green, blue)]):
        self.fail('out_of_range')

    return Color(red, green, blue)
```
이 스타일은 오류 메시지를 코드에서보다 명확하게 분리하고 선호해야합니다.

## Third party packages
다음의 타사 패키지도 제공됩니다.

### DRF Compound Fields
[drf-compound-fields](https://drf-compound-fields.readthedocs.io/en/latest/) 패키지는 `many=True`옵션을 사용하는 serializer가 아닌 다른 필드로 설명 할 수 있는 간단한 값 목록과 같은 "compound(복합)" serializer 필드를 제공합니다. 또한 특정 유형 또는 해당 유형의 항목 목록 일 수 있는 입력 된 dict 및 값에 대한 필드가 제공됩니다.

### DRF Extra Fields
[drf-extra-fields](https://github.com/Hipo/drf-extra-fields)패키지는 `Base64ImageField` 및 `PointField` 클래스를 포함하여 REST 프레임워크에 대한 추가 serializer 필드를 제공합니다.

### djangrestframework-recursive
[djangorestframework-recursive](https://github.com/heywbj/django-rest-framework-recursive) 패키지는 재귀적 구조의 serializer와 deserializer를 위한 `RecursiceField`를 제공합니다.

### django-rest-framework-gis
[django-rest-framework-gis](https://github.com/djangonauts/django-rest-framework-gis) 패키지는 `GeometryField` 필드와 GeoJSON serializer 같은 django rest 프레임워크를 위한 지리적 추가 기능을 제공합니다.

### django-rest-framework-hstore
[django-rest-framework-hstore](https://github.com/djangonauts/django-rest-framework-hstore) 패키지는 [django-hstore](https://github.com/djangonauts/django-hstore) `DictionaryField` 모델 필드를 지원하는 `HStoreField`를 제공합니다.
