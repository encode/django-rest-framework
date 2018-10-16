# Django REST Framework - Validators

---

_"Validators can be useful for re-using validation logic between different types of fields."_  


_"유효성 검사기는 다른 유형의 필드간에 유효성 검사논리를 다시 사용하는데 유용할 수 있습니다."_  

_— Django documentation_

---

## Validators(유효성 검사기)
대부분 REST 프레임워크에서 유효성 검사를 처리하는 경우 기본 필드 유효성 검사에 의존하거나 serializer 또는 필드 클래스에 대한 명시적인 `Validator` 메소드를 작성하기만 하면 됩니다.  
그러나 때때로 유효성 검사 논리를 재사용 가능한 구성 요소에 배치하여 코드 베이스 전체에서 쉽게 재사용 할 수 있습니다. 이 작업은 Validator 함수와 Validators 클래스를 사용하여 수행할 수 있습니다.

### Validation in REST framework
Django의 REST 프레임워크 serializer의 validation는 Django의 `ModelForm`클래스에서  validation이 작동하는 방식과 조금 다르게 처리됩니다.  
`ModelForm`을 사용하면 validation이 부분적으로 form에서 수행되고, 부분적으로 모델 인스턴스에서 수행됩니다. REST 프레임워크를 사용하면 validation은 전체적으로 serializer클래스에서 수행됩니다. 이는 다음과 같은 이유로 유리합니다.

- 적절한 구분을 제공하여 코드 동작을 보다 명확하게 만듭니다.
- shortcut `ModelSerializer`클래스를 사용하거나 명시적 serializer클래스를 사용하는 것은 쉽게 전환할 수 있습니다. `ModelSerializer`에 사용되는 모든 validation 동작은 복제가 간단합니다.
- serializer 인스턴스의 `repr`을 출력(print)하면 validation 규칙이 정확하게 표시됩니다. 모델 인스턴스에서 추가 숨겨진 validation 동작이 호출되지 않습니다.
`ModelSerializer`를 사용하면 모든 것이 자동으로 처리됩니다. 대신 Serializer클래스를 사용하여 드롭다운하려면 validation 규칙을 명시적으로 정의해야 합니다.

#### Example
REST 프레임워크가 명시적 validation을 사용하는 방법의 예로, 고유성 제약 조건이 있는 필드가 있는 간단한 모델 클래스를 사용합니다.

```python
class CustomerReportRecord(models.Model):
    time_raised = models.DateTimeField(default=timezone.now, editable=False)
    reference = models.CharField(unique=True, max_length=20)
    description = models.TextField()
```
다음은 `CustomReportRecord`인스턴스를 생성하거나 업데이트할 때 사용할 수 있는 기본 `ModelSerializer`입니다.

```python
class CustomerReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerReportRecord
```
`manage.py` shell을 사용하여 Django shell을 열면 이제 할 수 있습니다.

```python
>>> from project.example.serializers import CustomerReportSerializer
>>> serializer = CustomerReportSerializer()
>>> print(repr(serializer))
CustomerReportSerializer():
    id = IntegerField(label='ID', read_only=True)
    time_raised = DateTimeField(read_only=True)
    reference = CharField(max_length=20, validators=[<UniqueValidator(queryset=CustomerReportRecord.objects.all())>])
    description = CharField(style={'type': 'textarea'})
```
여기서 흥미로운 부분은 참조필드입니다. 고유성 제약이 serializer 필드의 validator에 의해 명시적으로 적용되고 있음을 알 수 있습니다.  
더 명시적인 스타일 때문에 REST 프레임워크는 Django의 핵심에서 사용할 수 없는 몇가지 validator 클래스를 포함합니다. 이 클래스들은 아래에 자세히 설명되어 있습니다.

---

### UniqueValidator
validator를 사용하여 모델 필드에 `unique=True`제약 조건을 적용 할 수 있습니다. 하나의 필수 인수와 선택적 `massages` 인수를 취합니다.

- `queryset` (필수) : 유일성을 강요해야하는  queryset입니다.
- `massege` : 검증이 실패했을 경우 사용하는 에러 메세지
- `lookup` : 검증되고 있는 값을 가지고 기존의 인스턴스를 찾는데 사용합니다. 기본값은 `exact`입니다.

이 validator는 다음과 같이 serializer 필드에 적용되어야 합니다.

```python
from rest_framework.validators import UniqueValidator

slug = SlugField(
    max_length=100,
    validators=[UniqueValidator(queryset=BlogPost.objects.all())]
)
```

### UniqueTogetherValidator
이 validator를 사용하여 모델 인스턴스에 `unique_together`제약 조건을 적용할 수 있습니다. 여기에는 두 개의 필수 인수와 단일 선택적 `messages`인수가 있습니다.

- `queryset`(필수) : 유일성을 강요해야하는 queryset입니다.
- `fields`(필수) : 고유한 set을 만들어야 하는 필드이름의 list 또는 tuple. 이들은 serializer 클래스의 필드로 존재해야 합니다.
- `message` : 검증에 실패했을 경우 사용하는 에러 메세지

validator는 다음과 같이 serializer 클래스에 적용되어야 합니다.

```python
from rest_framework.validators import UniqueTogetherValidator

class ExampleSerializer(serializers.Serializer):
    # ...
    class Meta:
        # ToDo items belong to a parent list, and have an ordering defined
        # by the 'position' field. No two items in a given list may share
        # the same position.
        validators = [
            UniqueTogetherValidator(
                queryset=ToDoItem.objects.all(),
                fields=('list', 'position')
            )
        ]
```

---
**Note**: `UniqueTogetherValidation`클래스는 항상 적용되는 모든 필드가 항상 필요한 것으로 처리된다는 암시적 제약조건을 부과합니다. `default`가 있는 필드는 사용자 입력에서 생략 된 경우에도 항상 값을 제공하므로 예외입니다.

---

### UniqueForDateValidator
### UniqueForMonthValidator
### UniqueForYearValidator
이 validator는 모델 인스턴스에 대해 `unique_for_date`, `unique_for_month`, `unique_for_year` 제약조건을 적용하는데 사용할 수 있습니다.

- `queryset`(필수) : 유일성을 강요해야하는 queryset입니다.
- `field`(필수) : 지정된 날짜 범위의 고유성에 대한 필드 이름입니다. 이것은 serializer 클래스의 필드로 존재해야합니다.
- `date_field`(필수) : 고유성 제한 조건의 날짜 범위를 결정하는데 사용할 필드 이름입니다. 이것은 serializer클래스의 필드로 존재해야 합니다.
- `massege` : 검증이 실패했을 경우에 사용하는 에러 메세지

validator는 다음과 같이 serializer클래스에 적용되어야 합니다.

```python
from rest_framework.validators import UniqueForYearValidator

class ExampleSerializer(serializers.Serializer):
    # ...
    class Meta:
        # Blog posts should have a slug that is unique for the current year.
        validators = [
            UniqueForYearValidator(
                queryset=BlogPostItem.objects.all(),
                field='slug',
                date_field='published'
            )
        ]
```
validation에 사용되는 날짜 필드는 항상 serializer클래스에 있어야 합니다. validation이 실행될 때까지 기본값에 사용되는 값이 생성되지 않기 때문에 모델 클래스 `default=...`에 의존할 수 없습니다.  
API를 어떻게 동작시키는지에 따라 이 스타일을 사용할 수 있는 스타일이 몇가지 있습니다. `ModelSerializer`를 사용하는 경우 REST 프레임워크에서 생성하는 기본값을 사용하는 것이 좋지만 serializer를 사용하거나 보다 명시적인 제어를 원한다면 아래에 설명된 스타일을 사용하세요.

#### Using with a writable date field. (쓰기 가능한 날짜 필드와 함께 사용하기)
날짜 필드를 쓰기 가능하게하려면, 기본 인수를 설정하거나 `required=True`를 설정하여 입력 데이터에서 항상 사용할 수 있도록 해야합니다.

```
published = serializers.DateTimeField(required=True)
```

#### Using with a read-only date field. (읽기 전용 날짜 필드와 함께 사용하기)
사용자가 날짜 필드를 볼 수는 있지만 편집할 수도 없도록 하려면 `read_only=True`로 설정하고 추가로 `default=...`인수를 설정하십시오.

```
published = serializers.DateTimeField(read_only=True, default=timezone.now)
```
필드는 사용자에게 쓸 수 없지만 기본값은 여전히 `validated_data`로 전달됩니다.

#### Using with a hidden date field. (숨겨진 날짜 필드와 함께 사용하기)
사용자가 날짜 필드를 완전히 숨기려면 `HiddenField`를 사용하세요. 이 필드 타입은 사용자 입력을 허용하지 않고 대신 항상 기본값을 serializer의 `validated_data`로 반환합니다.

```
published = serializers.HiddenField(default=timezone.now)
```

---
**Note**: `UniqueFor<Range>Validation`클래스는 적용되는 필드가 항상 필요한 것으로 처리된다는 암시적 제약조건을 적용합니다. `default`가 있는 필드는 사용자 입력에서 생략된 경우에도 항상 값을 제공하므로 예외입니다.

---

## Advanced field defaults
serializer의 여러 필드에 적용되는 valistor는 API 클라이언트가 제공해서는 안되지만 validator의 입력으로 사용할 수 있는 필드 입력이 필요할 수 있습니다.  
이러한 유형의 validation에 사용할 수 있는 두가지 패턴은 다음과 같습니다.

- `HiddenField`를 사용하는 것입니다. 이 필드는 `validated_data`에 있지만 serializer 출력 표현에서는 사용되지 않습니다.
- `read_only=True`와 함께 표준 필드는 사용하지만 `default=...`인수도 포함합니다. 이 필드는 serializer 출력 표현에 사용되지만 사용자가 직접 설정할 수는 없습니다.

REST 프레임워크는 이 컨텍스트에서 유용 할 수 있는 몇 가지 기본값을 포함합니다.

### CurrentUserDefault
현재 사용자를 나타내는데 사용할 수 있는 기본 클래스입니다. 이것을 사용하기 위해서는, serializer를 인스턴스화 할때 `request`가 컨텍스트 dict의 일부로 제공되어야 합니다.

```python
owner = serializers.HiddenField(
    default=serializers.CurrentUserDefault()
)
```

### CreateOnlyDefault
작성 조작 중 default의 인수만을 설정하는데 사용할 수 있는 기본 클래스. 업데이트 중 필드는 생략됩니다.  
이것은 작성 작업중에 사용되는 기본값이거나 호출 가능한 단일 인수를 취합니다.

```python
created_at = serializers.DateTimeField(
    read_only=True,
    default=serializers.CreateOnlyDefault(timezone.now)
)
```

---
## Limitations of validators
`ModelSerializer`이 생성하는 기본 serializer 클래스를 사용하는 대신 validation을 명시적으로 처리해야하는 모호한 경우가 있습니다.  
이러한 경우 serializerz `Meta.valisators`속성에 대한 빈 목록을 지정하여 자동 생성 된 validator를 사용하지 않도록 설정할 수 있습니다.

### Optional fields
기본적으로 "unique together"validation는 모든 필드가 `required=True`인지 확인합니다. 경우에 따라 필드 중 하나에 명시적으로 `required=False`를 적용하면 원하는 validation 동작이 모호할 수 있습니다.  
이 경우 일반적으로 serializer 클래스에서 validator를 제외하고, `.validate()`메서드나 뷰에서 validation 논리를 명시적으로 작성해야합니다.

예를 들어:

```python
class BillingRecordSerializer(serializers.ModelSerializer):
    def validate(self, data):
        # Apply custom validation either here, or in the view.

    class Meta:
        fields = ('client', 'date', 'amount')
        extra_kwargs = {'client': {'required': 'False'}}
        validators = []  # Remove a default "unique together" constraint.
```

### Updating nested serializers
기존 인스턴스에 업데이트를 적용할 때 고유성 validator는 현재 인스턴스를 고유성 검사에서 제외합니다. 현재 인스턴스는 고유성 검사의 컨텍스트에서 사용 할 수 있습니다. 이 속성은 serializer의 속성으로 존재하기 때문에 처음에는 serializer를 인스턴스화 할때 `instance=...`를 사용하여 전달되었습니다.  
중첩 된 serializer에 대한 업데이트 작업의 경우 인스턴스를 사용할 수 없으므로 이 배제를 적용할 방법이 없습니다.  
다시 말하면, serializer클래스에서 validator를 명시적으로 제거하고 validation 제약 조건에 대한 코드를 명시적으로 `.validate()`메서드나 뷰에 작성하려고 합니다.

### Debugging complex cases
`ModelSerializer` 클래스가 어떤 동작을 하는지 확실히 모를 경우 `manage.py` 셸을 실행하고 serializer의 인스턴스를 인쇄하면 자동으로 생성되는 필드와 validator를 검사 할 수 있습니다.

```python
>>> serializer = MyComplexModelSerializer()
>>> print(serializer)
class MyComplexModelSerializer:
    my_fields = ...
```
또한 복잡한 경우에는 기본 `ModelSerializer` 동작을 사용하는 대신 serializer 클래스를 명시적으로 정의하는 것이 더 나을 수 있습니다.

---

## Writing custom validators
Django의 기존 validator를 사용하거나 custom validator를 작성할 수 있습니다.

### Function based
validator는 아마도 실패하면 `serializer.ValidationError`를 발생시켜 호출합니다.

```python
def even_number(value):
    if value % 2 != 0:
        raise serializers.ValidationError('This field must be an even number.')
```
#### Field-level validation
Serializer 서브 클래스에 `.validate_<field_name>` 메소드를 추가하여 custom 필드 레벨 vallidation을 지정 할 수 있습니다.

### Class-based
클래스 기반 validator를 작성하려면 `__call__`메서드를 사용하세요. 클래스 기반 validator는 동작을 매개 변수화하고 다시 사용할 수 있으므로 유용합니다.

```python
class MultipleOf(object):
    def __init__(self, base):
        self.base = base

    def __call__(self, value):
        if value % self.base != 0:
            message = 'This field must be a multiple of %d.' % self.base
            raise serializers.ValidationError(message)
```

#### Using `set_context()`

일부 고급 예제에서는 validator를 추가 컴텍스트로 사용되는  serializer 필드로 전달해야 할 수 있습니다. 클래스 기반의 validator에서 `set_context`메서드를 선언하여 그렇게 할 수 있습니다.

```python
def set_context(self, serializer_field):
    # Determine if this is an update or a create operation.
    # In `__call__` we can then use that information to modify the validation behavior.
    self.is_update = serializer_field.parent.instance is not None
```