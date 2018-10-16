# Django REST framework - Serializers

---

_"Expanding the usefulness of the serializers is something that we would like to address. However, it's not a trivial problem, and it will take some serious design work."  
"serializer의 유용성을 확장하는 것은 우리가 다루고자 하는 것입니다. 그러나, 그것은 사소한 문제가 아니며. 심각한 디자인 작업을 필요로 합니다."  
— Russell Keith-Magee  _

## Serializers

Serializers는 쿼리셋들 및 모델 인스턴스와 같은 복잡한 데이터를 `JSON`, `XML` 또는 기타 컨텐트 유형으로 쉽게 렌더링 할 수 있는 Python 기본 데이터 유형으로 변환해 줍니다. 또한 serializer는 deserialization을 제공하여, 들어오는 데이터의 유효성을 처음 확인한 후에 구문 분석 된 데이터를 복합 형식으로 다시 변환 할 수 있습니다.  
>
>`DJango`에서 `Client`으로 복잡한 데이터(모델 인스턴스 등)를 보내려면 'string'으로 변환해야합니다. 이 변환을 **`serializer`** 라고 합니다. 반대로 `client`의 'string'을 Djagno로 받을 때 Python 기본 데이터 유형으로 받아야 하는데 이 변환을 **`deserializer`**라고 합니다.

REST 프레임워크의 serializers는 Django의 `Form` 및 `modelForm` 클래스와 매우 유사하게 작동합니다. REST 프레임워크는 `ModelSerializer`(모델 인스턴스와 쿼리셋을 다루는 시리얼라이저를 생성하기 유용한 클래스)뿐만 아니라 응답의 출력을 제어하는 강력하고 일반적인 방법을 제공하는 `Serializer` 클래스를 제공합니다.

### Declaring Serializers
예제를 위해 사용할 간단한 객체를 만들어 봅니다.

```python
from datetime import datetime

class Comment(object):
    def __init__(self, email, content, created=None):
        self.email = email
        self.content = content
        self.created = created or datetime.now()

comment = Comment(email='leila@example.com', content='foo bar')
```
`comment`객체에 해당하는 데이터를 serializer 및 deserializer화하는데 사용할 수 있는 serializer를 선언합니다.

serializer를 선언하면 양식을 선언하는 것과 매우 유사합니다.

```python
from rest_framework import serializers

class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()
```

### Serializing objects
`CommentSerializer`를 사용하여 주석 또는 주석 목록을 serializer 할 수 있습니다. 다시 말하면, `Serializer`클래스를 사용하는 것은 `Form`클래스를 사용하는 것과 비슷합니다.

```
serializer = CommentSerializer(comment)
serializer.data
# {'email': 'leila@example.com', 'content': 'foo bar', 'created': '2016-01-27T15:17:10.375877'}
```
이 시점에서 모델 인스턴스를 파이썬 기본 데이터 유형으로 변환했습니다. serializer 과정을 마무리하기 위해 데이터를 `json`으로 렌더링합니다.

```
from rest_framework.renderers import JSONRenderer

json = JSONRenderer().render(serializer.data)
json
# b'{"email":"leila@example.com","content":"foo bar","created":"2016-01-27T15:17:10.375877"}'
```

### Deserializing objects
Deserialization도 비슷합니다. 먼저 파이썬 데이터 형식으로 스트림을 파싱합니다.

```python
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

stream = BytesIO(json)
data = JSONParser().parse(stream)
```
그런 다음 기본 데이터 유형을 검증 된 데이터 dict로 복원합니다.

```
serializer = CommentSerializer(data=data)
serializer.is_valid()
# True
serializer.validated_data
# {'content': 'foo bar', 'email': 'leila@example.com', 'created': datetime.datetime(2012, 08, 22, 16, 20, 09, 822243)}
```

### Saving instances
유효성이 검사 된 데이터를 기반으로 완전한 객체 인스턴스를 반환하려면, `.create()`, `update()`메소드 중 하나나 둘 모두를 구현해야합니다. 예를 들어:

```python
class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()

    def create(self, validated_data):
        return Comment(**validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.content = validated_data.get('content', instance.content)
        instance.created = validated_data.get('created', instance.created)
        return instance
```
객체 인스턴스가 Django 모델과 일치하는 경우 이 메소드가 객체를 데이터베이스에 저장하도록 해야합니다. 예를 들어, `Comment`가 Django 모델인 경우 메소드는 다음과 같습니다.

```python
def create(self, validated_data):
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.content = validated_data.get('content', instance.content)
        instance.created = validated_data.get('created', instance.created)
        instance.save()
        return instance
```
이제 테이터를 deserializer 할 때 `.save()`를 호출하여 유효성이 검사된 데이터를 기반으로 객체 인스턴스를 반환 할 수 있습니다.

```
comment = serializer.save()
```
`.save()`를 호출하면 serializer 클래스를 인스턴스화 할 때 기존 인스턴스가 전달되었는지 여부에 따라 새 인스터스를 만들거나 기존 인스턴스를 업데이트합니다.

```
# .save() will create a new instance.
serializer = CommentSerializer(data=data)

# .save() will update the existing `comment` instance.
serializer = CommentSerializer(comment, data=data)
```
`.create()` 및 `.update()` 메서드는 모두 선택사항입니다. serializer 클래스의 유사 케이스에 따라 하나 또는 둘 모두 구현 할 수 있습니다.

#### 추가 속성을 `.save()`에 전달합니다.

때로는 인스턴스를 저장하는 시점에 뷰 코드가 데이터를 추가할 수 있어야합니다. 이 추가 데이터에는 현재 사용자, 현재 시간 또는 요청 데이터의 일부가 아닌 다른 정보가 포함될 수 있습니다.

`.save()`를 호출 할 때 추가 키워드 인수를 포함시켜서 그렇게 할 수 있습니다.

```
serializer.save(owner=request.user)
```
추가 키워드 인수는 `.create()` 또는 `.update()`가 호출 될 때 `validated_data`인수에 포함됩니다.

#### `.save()`를 직접 재정의 하세요.

어떤 경우에는 `.create()` 및 `.update()`메소드 이름이 의미가 없을 수 있습니다. 예를 들어, 문의 양식에서 새 인스턴스를 만드는 대신 email이나 다른 메세지를 보냅니다.  
이러한 경우에 대신 `.save()`를 직접 읽고 무시할 수 있습니다.

예를 들어:

```
class ContactForm(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField()

    def save(self):
        email = self.validated_data['email']
        message = self.validated_data['message']
        send_email(from=email, message=message)
```
위의 경우 serializer의 `.validated_data`속성에 직접 액서스해야 합니다.

### Validation
데이터를 deserializer 할 때 유효성이 검사 된 데이터에 액서스하기 전에 항상 `is_valid()`를 호출하거나 객체 인스턴스를 저장해야 합니다. 유효성 검사 오류가 발생하면, `.errors`속성에는 결과 오류 메세지를 나타내는 dict이 포함됩니다. 예를 들어:

```
serializer = CommentSerializer(data={'email': 'foobar', 'content': 'baz'})
serializer.is_valid()
# False
serializer.errors
# {'email': [u'Enter a valid e-mail address.'], 'created': [u'This field is required.']}
```
dict의 각 키는 필드 이름이며, 값은 해당 필드에 해당하는 오류 메시지의 문자열 목록입니다. `non_field_errors`키가 있을 수도 있고 일반적인 유효성 검사 오류를 나열합니다. `non_field_errors` 키의 이름은 REST 프레임 워크 설정의 `NON_FIELD_ERRORS_KEY`을 사용하여 사용자 정의 할 수 있습니다.  

항목 목록을 deserializer 할 때 오류는 각 deserializer화 항목을 나타내는 dict 목록으로 반환됩니다.

#### 유효하지 않은 데이터에 대한 예외 발생
`.is_valid()`메서드는 유효성 검사 오류가 있는 경우 `serializers.ValidationError` 예외를 발생시키는 선택적 `raise_exception` 플래그를 사용합니다.  

이러한 예외는 REST 프레임워크에서 제공하는 기본 예외 처리기에서 자동으로 처리되며, 기본적으로 `HTTP 400 ad Request` 응답을 반환합니다.

```
# Return a 400 response if the data was invalid.
serializer.is_valid(raise_exception=True)
```

#### 필드 레벨 검증
Serializer 서브 클래스에 `.validate_<field_name>`메소드를 추가하여 custom 필드 레벨 유효성 검증을 지정할 수 있습니다. 이것들은 Django form의 `.clean_<field_name>`메소드와 비슷합니다.

이 메소드는 인수가 필요하며, 유효성 검사가 필요한 필드 값입니다.
`validate_<field_name>` 메소드는 유효한 값을 반환하거나 `serializers.ValidationError`를 발생시켜야합니다.
예를 들어:

```
from rest_framework import serializers

class BlogPostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    content = serializers.CharField()

    def validate_title(self, value):
        """
        Check that the blog post is about Django.
        """
        if 'django' not in value.lower():
            raise serializers.ValidationError("Blog post is not about Django")
        return value
```

---
**NOTE** : `<field_name>`이 `required=False` parameter를 사용하여 `serializer`에서 선언 된 경우, 필드가 포함되어 있지 않으면 이 유효성 검사 단계가 수행되지 않습니다.

---
#### 객체 수준 유효성 검사
여러 필드에 대한 액서스가 필요한 다른 유효성 검사를 하려면, Serializer 서브 클래스에 `.validate()` 메소드를 추가하세요.
이 메소드는 필드 값의 dict인 단일 인수를 취합니다. 필요한 경우 `ValidationError`를 발생시키거나 유효성 검사 된 값을 반환해야 합니다. 예를 들면:

```python
from rest_framework import serializers

class EventSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=100)
    start = serializers.DateTimeField()
    finish = serializers.DateTimeField()

    def validate(self, data):
        """
        Check that the start is before the stop.
        """
        if data['start'] > data['finish']:
            raise serializers.ValidationError("finish must occur after start")
        return data
```

#### Validators (검사기)
Serializer의 개별 필드는 필드 인스턴스에 선언함으로써 유효성 검사기에 포함할 수 있습니다.

```
def multiple_of_ten(value):
    if value % 10 != 0:
        raise serializers.ValidationError('Not a multiple of ten')

class GameRecord(serializers.Serializer):
    score = IntegerField(validators=[multiple_of_ten])
    ...
```
또한 Serializer 클래스에는 전체 필드 데이터 집합에 적용되는 재사용 가능한 유효성 검사기가 포함될 수 있습니다. 이 유효성 검사기는 `Meta`클래스에 선언함으로써 포함됩니다.

```
class EventSerializer(serializers.Serializer):
    name = serializers.CharField()
    room_number = serializers.IntegerField(choices=[101, 102, 103, 201])
    date = serializers.DateField()

    class Meta:
        # Each room only has one event per day.
        validators = UniqueTogetherValidator(
            queryset=Event.objects.all(),
            fields=['room_number', 'date']
        )
```
더 많은 정보는  [validators documentation](http://www.django-rest-framework.org/api-guide/validators/)를 참조하세요.

### Accessing the initial data and instance (초기 데이터 및 인스턴스 액서스)
serializer 인스턴스에 초기 객체 또는 쿼리셋을 전달 할 때 객체는 `.instance`로 사용 가능합니다. 초기 객체가 전달되지 않으면 `.instance`속성이 `None`이 됩니다.

데이터를 serializer 인스턴스에 전달 할 때 수정되지 않은 데이터는 `.initial_data`로 사용 가능합니다. data 키워드 인수가 전달되지 않으면 `.initial_data`속성이 존재 하지 않습니다.

### Partial updates (부분 업데이트)
기본적으로 serializer는 모든 필수 필드에 값을 전달해야하며 그렇지 않으면 유효성 검사 오류가 발생합니다. partial 업데이트를 허용하기 위해 `partial`인수를 사용 할 수 있습니다.

```
# Update `comment` with partial data
serializer = CommentSerializer(comment, data={'content': u'foo bar'}, partial=True)
```

### Dealing with nested objects (중첩된 객체 다루기)
앞의 예제는 단순한 데이터 유형만을 가진 객체를 다루는 경우에는 문제가 없지만 객체의 일부 속성이 문자열, 날짜 또는 정수와 같은 단순한 데이터 유형이 아닌 복잡한 객체를 표현할 수 있어야하는 경우가 있습니다.

Serializer 클래스 자체는 Field 유형이며, 한 객체 유형이 다른 객체 유형 내에 중첩되어있는 관계를 나타내는데 사용할 수 있습니다.

```python
class UserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=100)

class CommentSerializer(serializers.Serializer):
    user = UserSerializer()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()
```
중첩 된 표현이 `None`값을 선택적으로 받아 들일 수 있으면 `required=False`플래그를 중첩 된 serializer에 전달해야 합니다.

```python
lass CommentSerializer(serializers.Serializer):
    user = UserSerializer(required=False)  # May be an anonymous user.
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()
```
마찬가지로 중첩 표현이 항목 목록이어야하는 경우 중첩 된 serializer에 `many=True` 플래그를 전달해야 합니다.

```python
class CommentSerializer(serializers.Serializer):
    user = UserSerializer(required=False)
    edits = EditItemSerializer(many=True)  # A nested list of 'edit' items.
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()
```

### Writable nested representations (쓰기 가능한 중첩 표현)
데이터의 deserializer를 지원하는 중첩 된 표현을 처리할 때, 중첩 된 객체의 오류는 중첩 된 객체의 필드 이름 아래에 중첩됩니다.

```
serializer = CommentSerializer(data={'user': {'email': 'foobar', 'username': 'doe'}, 'content': 'baz'})
serializer.is_valid()
# False
serializer.errors
# {'user': {'email': [u'Enter a valid e-mail address.']}, 'created': [u'This field is required.']}
```
비슷하게, `.validated_data`속성은 중첩 된 데이터 구조를 포함합니다.

#### 중첩 된 표현을 위한 `.create()` 메소드 작성하기
쓰기 가능한 중첩 표현을 지원하려면 여러 객체를 저장하는 `.create()` 또는 `.update()`메소드를 작성해야 합니다.

다음 예제는 중첩 된 프로필 객체가 있는 사용자 만들기를 처리하는 방법을 보여줍니다.

```python
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ('username', 'email', 'profile')

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        user = User.objects.create(**validated_data)
        Profile.objects.create(user=user, **profile_data)
        return user
```
#### 중첩 된 표현을 위해 `.update()`메소드 작성하기
업데이트의 경우, 관계 업데이트를 처리하는 방법에 대해 신중하게 생각해야합니다. 예를 들어, 관계에 대한 데이터가 없거나 제공되지 않은 경우 어떤 일이 일어나야 할까요?

- 관계를 데이터베이스에서 `NULL`로 설정하세요.
- 연관된 인스턴스를 삭제하세요.
- 데이터를 무시하고 인스턴스를 있는 그대로 두세요.
- 유효성 검증 오류를 발생시키세요.

다음은 이전 UserSerializer 클래스의 `update()`메소드 예제입니다.

```python
 def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        # Unless the application properly enforces that this field is
        # always set, the follow could raise a `DoesNotExist`, which
        # would need to be handled.
        profile = instance.profile

        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        profile.is_premium_member = profile_data.get(
            'is_premium_member',
            profile.is_premium_member
        )
        profile.has_support_contract = profile_data.get(
            'has_support_contract',
            profile.has_support_contract
         )
        profile.save()

        return instance
```
중첩 된 생성 및 업데이트의 동작이 애매할 수 있고, 관련 모델간에 복잡한 종속성이 필요할 수 있기 때문에 REST 프레임워크3 에서는 이러한 메서드를 항상 명시적을 작성해야 합니다. 기본적을 `ModelSerializer`, `.create()`, `.update()`메소드는 쓰기 가능한 중첩 표현데 대한 지원을 포함하지 않습니다.  

자동으로 기입 가능한 중첩 표현의 일부를 서포트하는 패키지가 3.1 릴리스와 함께 릴리스 될 가능성도 있습니다.

#### 모델 관리자 클래스에서 관련 인스턴스 저장 처리
serializer에 여러 관련 인스턴스를 저장하는 대신 올바른 인스턴스를 생성하는 custom 모델 관리자 클래스를 작성 할 수 있습니다.  

예를 들어, User 인스턴스와 Profile 인스턴스가 항상 쌍으로 함께 생성되도록하고 하고 싶다고 가정해보겠습니다. 다음과 같이 custom 매니저 클래스를 작성 할 수 있습니다.

```python
class UserManager(models.Manager):
    ...

    def create(self, username, email, is_premium_member=False, has_support_contract=False):
        user = User(username=username, email=email)
        user.save()
        profile = Profile(
            user=user,
            is_premium_member=is_premium_member,
            has_support_contract=has_support_contract
        )
        profile.save()
        return user
```
이 관리자 클래스는 이제 전보다 훌륭하게 사용자 인스턴스와 프로필 인스턴스가 항상 동시에 생성된다는 사실을 캡슐화합니다. serializer 클래스의 `.create()` 메서드를 새 관리자 매서드를 사용하도록 다시 작성 할 수 있습니다.

```python
def create(self, validated_data):
    return User.objects.create(
        username=validated_data['username'],
        email=validated_data['email']
        is_premium_member=validated_data['profile']['is_premium_member']
        has_support_contract=validated_data['profile']['has_support_contract']
    )
```
이 접근법에 대한 더 자세한 내용은 [model managers](https://docs.djangoproject.com/en/1.10/topics/db/managers/)와 [this blogpost on using model and manager classes](https://www.dabapps.com/blog/django-models-and-encapsulation/) 을 참조하세요.

### Dealing with multiple objects
Serializer 클래스는 객체 목록의 serializer 또는 deserializer를 처리 할 수도 있습니다.

#### 여러 객체 serializer

단일 객체 인스턴스 대신 쿼리셋 또는 객체 목록을 serializer하려면 serializer를 인스턴스화 할 때 `many=True`플래그를 전달해야 합니다. 그런 다름 serializer 할 쿼리셋이나 객체 목록을 전달 할 수 있습니다.

```
queryset = Book.objects.all()
serializer = BookSerializer(queryset, many=True)
serializer.data
# [
#     {'id': 0, 'title': 'The electric kool-aid acid test', 'author': 'Tom Wolfe'},
#     {'id': 1, 'title': 'If this is a man', 'author': 'Primo Levi'},
#     {'id': 2, 'title': 'The wind-up bird chronicle', 'author': 'Haruki Murakami'}
# ]
```

#### 여러 객체를 deserializer
여러 객체를 deserializer화하는 기본동작은 객체 생성을 지원하지만 여러 객체 업데이트를 지원하지 않습니다. 이러한 경우 중 하나를 지원하거나 사용자 지정하는 방법에 대한더 자세한 내용은 [ListSerializer](http://www.django-rest-framework.org/api-guide/serializers/#listserializer)를 참조하세요.

### Including extra context (추가 문맥 포함)
serializer되고 있는 객체에 추가로, serializer에 여분의 문맥을 제공 할 필요가 이는 경우가 있습니다. 한 가지 일반적인 경우는 하이퍼링크 된 관계를 포함하는 serializer를 사용하는 경우이며, serializer가 현재 요청에 액서스하여 정규화 된 URL을 제대로 생성 할 수 있어야합니다.  

serializer를 인스턴스화 할 때 컨텍스트 인수를 전달하여 임의의 추가 컨텍스트를 제공 할 수 있습니다. 예를 들어:

```
serializer = AccountSerializer(account, context={'request': request})
serializer.data
# {'id': 6, 'owner': u'denvercoder9', 'created': datetime.datetime(2013, 2, 12, 09, 44, 56, 678870), 'details': 'http://example.com/accounts/6/details'}
```
컨텍스드 dict은 사용자 정의`.to_representation()`메소드와 같은 serializer 필드 로직 내에서 `self.context`속성에 액서스하여 사용할 수 있습니다.

## ModelSerializer
종종 Django 모델 정의와 밀접하게 매핑되는 serializer 클래스가 필요합니다.  
`ModelSerializer`클래스는 모델 필드에 해당하는 필드가 있는 Serializer 클래스를 자동을 만들 수 있는 지름길을 제공합니다.

**`ModelSerializer`클래스는 다음을 제외하고는 일반 Serializer 클래스와 동일합니다.**

- 모델을 기반으로 일련의 필드가 자동으로 생성됩니다.
- unique_together validator와 같은 serializer에 대한 validator를 자동으로 생성합니다.
- `.create()`와 `.update()`의 간단한 기본 구현을 포함합니다.

`ModelSerializer` 선언은 다음과 같습니다.

```python
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'account_name', 'users', 'created')
```
기본적으로 클래스의 모든 모델 필드는 해당 serializer 필드에 매핑됩니다.

모델의 외래 키와 같은 관계는 `PrimaryKeyRelatedField`에 매핑됩니다. [역직렬화 관계 문서](http://www.django-rest-framework.org/api-guide/relations/)에 명시된대로 명식적으로 포함되지 않으면 기본적으로 역관계가 포함되지 않습니다.

### Inspecting a `ModelSerializer` (`ModelSerializer`을 검사)
Serializer 클래스는 유용한 필드 표현 문자열을 생성하므로, 필드의 상태를 완전히 검사 할 수 있습니다. 이는 자동으로 생성되는 필드 및 유효성 검사기들을 결정하려는 `ModelSerializer`로 작업 할 때 특히 유용합니다.  
이렇게 하려면, Django 쉘을 열어서 serializer 클래스를 가져와서 인스턴스화하고, 객체 표현을 출력하세요.

```
>>> from myapp.serializers import AccountSerializer
>>> serializer = AccountSerializer()
>>> print(repr(serializer))
AccountSerializer():
    id = IntegerField(label='ID', read_only=True)
    name = CharField(allow_blank=True, max_length=100, required=False)
    owner = PrimaryKeyRelatedField(queryset=User.objects.all())
```

### Specifying which fields to include (포함 할 필드 지정)
기본 필드의 하위 집합을 모델 serializer에서만 사용하려는 경우 `ModelForm`에서와 마찬가지로 필드를 사용하거나 옵션을 제외할 수 있습니다. `fields`속성을 사용하여 serializer해야하는 모든 필드를 명시적으로 설정하는 것이 좋습니다. 이렇게하면 모델이 변경 될 때 실수로 데이터가 노출 될 가능성이 줄어 듭니다.

예를 들어:

```python
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'account_name', 'users', 'created')
```
또한 `fields`속성을 특수 값 `'__all__'`으로 설정하여 모델의 모든 필드를 사용해야 함을 나타낼 수 있습니다.

예들 들면:

```python
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
```
serializer에서 제외 할 필드 목록에 `exclude`속성을 설정할 수 있습니다.

예를 들어:

```
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        exclude = ('users',)
```
위의 예에서 계정 모델에 `account_name`, `users`, `created` 필드가 3개 있는 경우, `account_name`필드가 만들어지고 serializer되도록 생성됩니다.  
필드 및 제외 속성의 이름은 일반적으로 모델 클래스의 모델 필드에 매핑됩니다.  
또는 필드 옵션의 이름은 모델 클래스에 존재하는 인수를 취하지 않는 속성이나 메서드에 매핑 할 수 있습니다.

### Specifying nested serialization (중첩 된 serializer 지정)
기본 `ModelSerializer`는 관계에 기본 키를 사용하지만 `depth` 옵션을 사용하여 중첩 된 표현을 쉽게 생성 할 수도 있습니다.

```python
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'account_name', 'users', 'created')
        depth = 1
```
`depth`옵션은 flat 표현으로 되돌리기 전에 탐색해야하는 관계의 깊이를 나타내는 정수 값으로 설정해야합니다.  
serializer가 수행되는 방식을 사용자 정의하려면 필드를 직접 정의해야합니다.

### Specifying fields explicitly (명시적으로 필드 지정하기)
`ModelSerializer`에 추가 필드를 추가하거나 Serializer 클래스에서와 마찬가지로 클래스의 필드를 선언하여 기본 필드를 재정의 할 수 있습니다.

```python
class AccountSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='get_absolute_url', read_only=True)
    groups = serializers.PrimaryKeyRelatedField(many=True)

    class Meta:
        model = Account
```
추가 필드는 모델의 모든 속성 또는 호출 가능 항목에 해당 할 수 있습니다.

### Specifying read only fields (읽기 전용 필드 지정하기)
여러 필드를 읽기 전용으로 지정할 수 있습니다. 각 필드는 `read_only=True` 특성을 명시적으로 추가하는 대신, 바로가기 메타 옵션인 `read_only_fields`를 사용할 수 있습니다.

이 옵션은 필드 이름의 목록이나 튜플이어야하며 다음과 같이 선언됩니다.

```python
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'account_name', 'users', 'created')
        read_only_fields = ('account_name',)
```
`editable=False`set과 `AutoField`필드가 있는 모델 필드는 기본적으로 읽기 전용으로 설정되며, `read_only_fields`옵션에 추가 할 필요가 없습니다.

---
**Note**: 읽기 전용 필드가 모델 수준에서 `unique_together` 제약 조건의 일부인 특별한 경우가 있습니다. 이 경우 필드는 제약 조건의 유효성을 검사하기 위해 serializer 클래스에서 필요하지만 사용자가 편집할 수 없도록 해야합니다.  
이를 처리하는 올바른 방법은 `read_only=True`와 `default=...`키워드 인수를 제공하여 serializer에서 필드를 명시적으로 지정하는 것입니다.  
한가지 예는 현재 인증 된 사용자에 대한 읽기 전용 관계이며다른 식별자와 고유합니다. 이 경우 사용자 필드를 다음과 같이 선언합니다.

```
user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
```
더 자세한 내용은 설명서를 참조하세요..
[Validators Documentation](http://www.django-rest-framework.org/api-guide/validators/), [UniqueTogetherValidator](http://www.django-rest-framework.org/api-guide/validators/#uniquetogethervalidator), [CurrentUserDefault](http://www.django-rest-framework.org/api-guide/validators/#currentuserdefault)

---

### Additional keyword arguments (추가 키워드 인수)
또한 `extra_kwargs`옵션을 사용하여 필드에 임의의 추가 키워드 인수를 지정할 수 있는 단축키가 있습니다. `read_only_fields`의 경우와 마찬가지로, 이것은 serializer에서 필드를 명시적으로 선언 할 필요가 없음을 의미합니다.  
이 옵션은 필드 이름을 키워드 인수 dict에 매핑하는 dict입니다. 예를 들면:

```python
class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
```
### Relational fields
모델 인스턴스를 serializer 할 때 관계를 나타내기 위해 선택할 수 있는 여러 방법들이 있습니다. `ModelSerializer`의 기본 표현은 관련 인스턴스의 기본 키를 사용하는 것입니다.  
다른 표현은 하이퍼링크를 사용하여 serializer, 완전한 중첩 표현을 serializer,사용자 정의 표현을 사용하여 serializer하는 것을 포함합니다.  
자세한 내용은 [ serializer relations ](http://www.django-rest-framework.org/api-guide/relations/)참조하세요.

### Customizing field mappings (사용자 정의 필드 매핑)
ModelSerializer 클래스는 serializer를 인스턴스화 할 때 serializer 필드가 자동으로 결정되는 방식을 변경하기 위해 재정의 할 수 있는 API도 제공합니다.  
일반적으로 ModelSerializer가 기본적으로 필요한 필드를 생성하지 않으면 클래스에 명시적으로 추가하거나 대신 일반 Serializer클래스를 사용해야 합니다. 그러나 경우에 따라 특정 모델에 대해 serializer 필드가 생성되는 방식을 정의하는 새 기본 클래스를 만들 수도 있습니다.

```
.serializer_field_mapping
```
Django 모델 클래스와 REST 프레임워크 serializer 클래스의 매핑.  
이 맵핑을 겹쳐 쓰면 각 모델 클래스에 사용해랴 하는 기본 serializer 클래스를 변경 할 수 있습니다.

```
.serializer_related_field
```
이 속성은 기본적으로 관계형 필드에 사용되는 serializer 필드 클래스이어야 합니다.  
`ModelSerializer`의 경우 기본값은 `PrimaryKeyRelatedField`입니다.  
`HyperlinkedModelSerializer`이 기본값이 `serializers.HyperlinkedRelatedField`입니다.

```
serializer_url_field
```
serializer의 `url`필드에 사용해야하는 serializer 필드 클래스입니다. `serializers.HyperlinkedIdentityField`가 기본값입니다.

```
serializer_choice_field
```
serializer의 선택 필드에 사용해야하는 serializer 필드 클래스입니다. `serializers.ChoiceField`가 기본값입니다.

#### The field_class and field_kwargs API
다음 메서드는 serializer에 자동으로 포함되어야 하는 각 필드의 클래스 및 키워드 인수를 결정하기 위해 호출됩니다. 이 메소드들은 각각 `(field_class, field_kwargs)`의 두 튜플을 리턴해야합니다.  

```
.build_standard_field(self, field_name, model_field)
```
표준 모델 필드에 매핑되는 serializer 필드를 생성하기 위해 호출됩니다. 디폴트의 구현은 `serializer_field_mapping`속성에 근거한 serializer 클래스를 돌려줍니다.

```
.build_relational_field(self, field_name, relation_info)
```
관계형 모델 필드에 매핑되는 serializer 필드를 생성하기 위해 호출됩니다.  
디폴트의 ​​구현은 `serializer_relational_field` 속성에 근거한 serializer 클래스를 돌려줍니다.  
`relation_info` 인수는 명명 된 튜플이며 `model_field`, `related_model`, `to_many` 및 `has_through_model` 속성을 포함합니다.

```
.build_nested_field(self, field_name, relation_info, nested_depth)
```
`depth`옵션이 설정 된 경우, 관계형 모델 필드에 매핑되는 serializer 필드를 생성하기 위해 호출됩니다.  
기본 구현은 `ModelSerializer`또는 `HtperlinkedModelSerializer`를 기반으로 중첩 된 serializer 클래스를 동적으로 만듭니다.  
`nested_delth`는 `depth`옵견의 값에서 1을 뺀 값입니다.  
`relation_info`인수는 명명 된 튜플이며, `model_field`, `related_model`, `to_many`, `has_through_model`속성을 포함합니다.

```
.build_property_field(self, field_name, model_class)
```
모델 클래스의 속성 또는 인수가 없는 메서드에 매핑되는 serializer 필드를 생성하기 위해 호출됩니다.  
기본 구현은 `readOnlyField` 클래스를 반환합니다.

```
.build_url_field(self, field_name, model_class)
```
serializer 자신의 `url` 필드에 대한 serializer 필드를 생성하기 위해 호출됩니다. 기본 구현은 `HyperlinkedIdentityField` 클래스를 반환합니다.

```
.build_unknown_field(self, field_name, model_class)
```
필드 이름이 모델 필드 또는 모델 속성에 매핑되지 않았을 때 호출됩니다. 서브 클래스에 의해 이 동작을 사용자 정의해도, 기본 구현에서는 에러가 발생합니다.

## HyperlinkedModelSerializer
`HyperlinkedModelSerializer` 클래스는 기본 키가 아닌 관계를 나타 내기 위해 하이퍼 링크를 사용한다는 점을 제외하고는 `ModelSerializer` 클래스와 유사합니다.  
기본적으로 serializer에는 기본 키 필드 대신 `url` 필드가 포함됩니다.  
url 필드는 `HyperlinkedIdentityField serializer` 필드를 사용하여 표현되며 모델의 모든 관계는 `HyperlinkedRelatedField` serializer 필드를 사용하여 표시됩니다.  
기본 키를 `fields` 옵션에 추가하여 명시적으로 포함시킬 수 있습니다. 예를 들어:

```python
class AccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Account
        fields = ('url', 'id', 'account_name', 'users', 'created')
```

### Absolute and relative URLs
`HyperlinkedModelSerializer`를 인스턴스화 할 때는 현재 `request`을 serializer 컨텍스트에 포함해야합니다. 예를 들면:

```python
serializer = AccountSerializer(queryset, context={'request': request})
```
이렇게하면 하이퍼링크에 적절한 호스트 이름이 포함될 수 있으므로 결과 표현은 다음과 같은 정규화 된 URL을 사용합니다.

```
http://api.example.com/accounts/1/
```
다음과 같은 상대 URL이 아닙니다.

```
/accounts/1/
```
상대 URL을 사용하려면 serializer 컨텍스트에서 `{ 'request': None}`을 명시적으로 전달해야합니다.

### How hyperlinked views are determined (하이퍼링크로 연결된 뷰가 결정되는 방법)
모델 인스턴스에 하이퍼링크하기 위해 어떤 뷰를 사용해야하는지 결정 할 수 있는 방법이 필요합니다.  
기본적으로 하이퍼링크는 `'{model_name} -detail'`스타일과 view 이름과 일치해야하며 `pk` 키워드 인수로 인스턴스를 찾습니다.  
다음과 같이 `extra_kwargs` 설정에서 `view_name`과 `lookup_field` 옵션 중 하나 또는 둘 모두를 사용하여 URL 필드 view 이름 및 조회 필드를 무시할 수 있습니다.

```python
class AccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Account
        fields = ('account_url', 'account_name', 'users', 'created')
        extra_kwargs = {
            'url': {'view_name': 'accounts', 'lookup_field': 'account_name'},
            'users': {'lookup_field': 'username'}
        }
```
또는 serializer에서 필드를 명시적으로 설정할 수 있습니다.

```
class AccountSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='accounts',
        lookup_field='slug'
    )
    users = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='username',
        many=True,
        read_only=True
    )

    class Meta:
        model = Account
        fields = ('url', 'account_name', 'users', 'created')
```

---
**tip**: 하이퍼 링크로 표시된 표현과 URL conf를 적절하게 일치시키는 것은 때로는 약간의 실수 일 수 있습니다. `HyperlinkedModelSerializer` 인스턴스의 `repr`을 인쇄하는 것은 관계가 매핑 할 것으로 예상되는 뷰 이름과 조회 필드를 정확하게 검사하는 데 특히 유용합니다.

---
### Changing the URL field name
URL 입력란의 이름은 'url'로 기본 설정됩니다. `URL_FIELD_NAME` 설정을 사용하여이를 전역으로 재정의 할 수 있습니다.

---
## ListSerializer
`ListSerializer` 클래스는 여러 개체를 한 번에 serialize하고 유효성을 검사하는 동작을 제공합니다.  
일반적으로 `ListSerializer`를 직접 사용할 필요는 없지만 대신 serializer를 인스턴스화 할 때 `many=True`를 전달해야합니다.  
serializer가 인스턴스화되고 `many=True`가 전달되면 `ListSerializer` 인스턴스가 만들어집니다. 그런 다음 serializer 클래스는 부모 `ListSerializer`의 자식이됩니다.  
다음 인수는 `ListSerializer`필드나 `many=True`로 전달되는 serializer에도 전달할 수 있습니다.

```
allow_empty
```
기본적으로 `True`이지만 빈 입력을 허용하지 않으려면 `False`로 설정할 수 있습니다.

### Customizing ListSerializer behavior
`ListSerializer` 동작을 사용자 정의하려는 경우가 몇 가지 있습니다.

- 특정 요소가 목록의 다른 요소와 충돌하지 않는지 확인하는 등 목록의 특정 유효성 검사를 제공하려고합니다.
- 여러 객체의 작성 또는 업데이트 동작을 사용자 정의하려고합니다.

이 경우 serializer 메타 클래스에서 `list_serializer_class` 옵션을 사용하여 `many=True`가 전달 될 때 사용되는 클래스를 수정할 수 있습니다.

``` python
class CustomListSerializer(serializers.ListSerializer):
    ...

class CustomSerializer(serializers.Serializer):
    ...
    class Meta:
        list_serializer_class = CustomListSerializer
```

#### Customizing multiple create(여러 작성 사용자 정의)
여러 객체 생성을위한 기본 구현은 목록의 각 항목에 대해 `.create()`를 호출하는 것입니다. 이 동작을 사용자 정의하려면 `many=True`가 전달 될 때 사용되는 `ListSerializer` 클래스에서 `.create()` 메서드를 사용자 정의해야합니다.

```
class BookListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        books = [Book(**item) for item in validated_data]
        return Book.objects.bulk_create(books)

class BookSerializer(serializers.Serializer):
    ...
    class Meta:
        list_serializer_class = BookListSerializer
```

#### Customizing multiple update(여러 업데이트 맞춤 설정)
기본적으로 `ListSerializer` 클래스는 다중 업데이트를 지원하지 않습니다. 이는 삽입 및 삭제에 대해 예상되는 동작이 모호하기 때문입니다.  
여러 업데이트를 지원하려면 명시적으로 업데이트해야합니다. 여러 개의 업데이트 코드를 작성할 때 다음 사항을 염두에 두십시오.

- 데이터 목록의 각 항목에 대해 어떤 인스턴스를 업데이트해야하는지 어떻게 결정합니까?
- 삽입을 어떻게 처리해야합니까? 그것들은 유효하지 않습니까? 아니면 새로운 objects를 만드나요?
- 제거물은 어떻게 처리해야합니까? 객체 삭제 또는 관계 제거를 의미합니까? 그들은 조용히 무시해야합니까, 아니면 무효합니까?
- 주문은 어떻게 처리해야합니까? 두 항목의 위치 변경은 상태 변경을 의미합니까 아니면 무시됩니까?

인스턴스 serializer에 명시적으로 `id` 필드를 추가해야합니다. 기본적으로 생성된 `id`필드는 `read_only`로 표시됩니다. 이로 인해 업데이트시 제거됩니다. 명시적으로 선언하면 목록 serializer의 `update` 메소드에서 사용할 수 있습니다.  
다음은 여러 업데이트를 구현하는 방법에 대한 예입니다.

```python
class BookListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        book_mapping = {book.id: book for book in instance}
        data_mapping = {item['id']: item for item in validated_data}

        # Perform creations and updates.
        ret = []
        for book_id, data in data_mapping.items():
            book = book_mapping.get(book_id, None)
            if book is None:
                ret.append(self.child.create(data))
            else:
                ret.append(self.child.update(book, data))

        # Perform deletions.
        for book_id, book in book_mapping.items():
            if book_id not in data_mapping:
                book.delete()

        return ret

class BookSerializer(serializers.Serializer):
    # We need to identify elements in the list using their primary key,
    # so use a writable field here, rather than the default which would be read-only.
    id = serializers.IntegerField()

    ...
    id = serializers.IntegerField(required=False)

    class Meta:
        list_serializer_class = BookListSerializer
```
REST 프레임워크2에 있는 `allow_add_remove` 동작과 유사한 업데이트 작업에 대한 것은 3.1 릴리스에 포함될 수 있습니다.

#### Customizing ListSerializer initialization (ListSerializer 초기화 사용자 정의)
`many=True`가 있는 serializer가 인스턴스화되면 자식 serializer 클래스와 상위 `ListSerializer` 클래스 모두에 대해 `.__ init __()` 메서드에 전달할 인수 및 키워드 인수를 결정해야합니다.  
디폴트의 ​​구현은, `validator`를 제외 해, 양쪽 모두의 클래스에 모든 인수를 건네주는 것입니다. 양쪽 모두는 customizer 키워드의 인수입니다. 양쪽 모두, 아이디 serializer 클래스를 대상으로하고 있습니다.
때때로 `many=True`가 전달 될 때 하위 클래스와 부모 클래스의 인스턴스화 방법을 명시적으로 지정해야 할 수도 있습니다. `many_init` 클래스 메소드를 사용하면 그렇게 할 수 있습니다.

```python
 @classmethod
    def many_init(cls, *args, **kwargs):
        # Instantiate the child serializer.
        kwargs['child'] = cls()
        # Instantiate the parent list serializer.
        return CustomListSerializer(*args, **kwargs)
```

## BaseSerializer
`BaseSerializer`는 serializer와 deserializer 스타일을 쉽게 지원하는데 사용할수 있는 대안입니다.  
이 클래스는 Serializer 클래스와 같은 기본 API를 구현합니다.  

- `.date` - 발신 기보 표현을 반환합니다.
- `.is_valid()` - 들어오는 데이터를 serializer 해제와 검증합니다.
- `.validated_data` - 검증 된 수신 데이터를 리턴합니다.
- `.errors` - 검증 중에 에러를 반환합니다.
- `.save()` - 검증 된 데이터를 객체 인스턴스에 저장합니다.

serializer 클래스에서 지원할 기능에 따라 무시할 수있는 네 가지 메서드가 있습니다.

- `.to_representation()` - 읽기 조작을 위해 serializer를 지원하려면 이를 오버라이드하세요.
- `.to_internal_value()` - 쓰기 조작을 위해 deserializer를 지원하려면 오버라이드하세요.
- `.create()`, `.update()` - 인스턴스 저장을 지원하기 위해 이들 중 하나나 둘다 무시하세요.

이 클래스는 Serializer 클래스와 동일한 인터페이스를 제공하기 때문에 일반 `Serializer` 또는 `ModelSerializer`에서 사용하던 것과 똑같이 기존 CBV와 함께 사용할 수 있습니다.  
`BaseSerializer` 클래스는 browsable API에서 HTML 양식을 생성하지 않는다는 점에서 주목할 것입니다. 이는 반환하는 데이터에 각 필드를 적절한 HTML 입력으로 렌더링 할 수 있는 모든 필드 정보를 포함하지 않기 때문입니다.

### Read-only `BaseSerializer` classes
`BaseSerializer` 클래스를 사용하여 읽기 전용 serializer를 구현하려면 `.to_representation()` 메서드를 재정의해야합니다. 간단한 Django 모델을 사용하는 예제를 살펴 보겠습니다.

```python
class HighScore(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    player_name = models.CharField(max_length=10)
    score = models.IntegerField()
```
`HighScore` 인스턴스를 원시 데이터 유형으로 변환하기위한 읽기 전용 serializer  컨버터를 만드는 것은 간단합니다.

```python
class HighScoreSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        return {
            'score': obj.score,
            'player_name': obj.player_name
        }
```
이제 이 클래스를 사용하여 단일 `HighScore` 인스턴스를 serializer 할 수 있습니다.

```python
@api_view(['GET'])
def high_score(request, pk):
    instance = HighScore.objects.get(pk=pk)
    serializer = HighScoreSerializer(instance)
    return Response(serializer.data)
```
또는 이를 사용하여 여러 인스턴스를 serializer할 수 있습니다.

```python
@api_view(['GET'])
def all_high_scores(request):
    queryset = HighScore.objects.order_by('-score')
    serializer = HighScoreSerializer(queryset, many=True)
    return Response(serializer.data)
```

### Read-write `BaseSerializer` classes
읽기-쓰기 serializer를 만들려면 먼저 `.to_internal_value()`메서드를 구현해야 합니다. 이 메서드는 객체 인스턴스를 구성하는데 사용 될 유효성이 있는 값을 반환하고 제공된 데이터가 잘못된 형식인 경우 ValidationError를 발생시킬 수 있습니다.  
`.to_internal_value()`를 구현하면 serializer에서 기본 유효성 검사 API를 사용할 수 있으며 `.is_valid()`, `.validated_data` 및 `.errors`를 사용할 수 있습니다.  
`.save()`도 지원하려면 `.create()` 및 `.update()` 메소드 중 하나 또는 모두를 구현해야합니다.  
다음은 읽기-쓰기 작업을 모두 지원하도록 업데이트 된 이전의 `HighScoreSerializer`의 전체 예제입니다.

```python
class HighScoreSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        score = data.get('score')
        player_name = data.get('player_name')

        # Perform the data validation.
        if not score:
            raise ValidationError({
                'score': 'This field is required.'
            })
        if not player_name:
            raise ValidationError({
                'player_name': 'This field is required.'
            })
        if len(player_name) > 10:
            raise ValidationError({
                'player_name': 'May not be more than 10 characters.'
            })

        # Return the validated values. This will be available as
        # the `.validated_data` property.
        return {
            'score': int(score),
            'player_name': player_name
        }

    def to_representation(self, obj):
        return {
            'score': obj.score,
            'player_name': obj.player_name
        }

    def create(self, validated_data):
        return HighScore.objects.create(**validated_data)
```

### Creating new base classes
`BaseSerializer` 클래스는 특정 serializer 스타일을 처리하거나 대체 저장 장치 백엔드와 통합하기 위해 새 generic serializer 클래스를 구현하려는 경우에도 유용합니다.  
다음 클래스는 임의의 객체를 기본 자료형으로 강제 변환 할 수 있는 일반 serializer 컨버터의 예입니다.

```python
class ObjectSerializer(serializers.BaseSerializer):
    """
    A read-only serializer that coerces arbitrary complex objects
    into primitive representations.
    """
    def to_representation(self, obj):
        for attribute_name in dir(obj):
            attribute = getattr(obj, attribute_name)
            if attribute_name('_'):
                # Ignore private attributes.
                pass
            elif hasattr(attribute, '__call__'):
                # Ignore methods and other callables.
                pass
            elif isinstance(attribute, (str, int, bool, float, type(None))):
                # Primitive types can be passed through unmodified.
                output[attribute_name] = attribute
            elif isinstance(attribute, list):
                # Recursively deal with items in lists.
                output[attribute_name] = [
                    self.to_representation(item) for item in attribute
                ]
            elif isinstance(attribute, dict):
                # Recursively deal with items in dictionaries.
                output[attribute_name] = {
                    str(key): self.to_representation(value)
                    for key, value in attribute.items()
                }
            else:
                # Force anything else to its string representation.
                output[attribute_name] = str(attribute)
```

## Advanced serializer usage (고급 사용법)

### Overriding serialization and deserialization behavior
serializer 클래스의 serialization, deserialization 또는 유효성 검사를 변경해야하는 경우 `.to_representation()` 또는 `.to_internal_value()` 메서드를 재정합니다.  
유용한 이유는 다음과 같습니다.

- 새로운 serializer 기본 클래스에 대한 새로운 동작을 추가
- 기존 클래스의 동작을 약간 수정합니다.
- 많은 양의 데이터를 반환하며 자주 액서스되는 API 엔드포인트의 serializer 성능 향상

이 메소드의 서명은 다음과 같습니다.

```
.to_representation(self, obj)
```
serializer가 필요한 객체 인스턴스를 가져와서 원시 표현을 반환해야합니다. 일반적으로 이것은 내장 파이썬 데이터 유형의 구조를 반환하는 것을 의미합니다. 처리 할 수 있는 정확한 유형은 API에 대해 구성한 렌더링 클래스에 따라 다릅니다.

```
.to_internal_value(self, data)
```
검증되지 않은 데이터를 입력 받아 `serializer.validated_data`로 사용할 수 있는 유효성이 검사 된 데이터를 반환해야합니다. serializer 클래스에서 `.save()`가 호출되면 반환 값도 `.create()` 또는 `.update()` 메서드에 전달됩니다.  
유효성 검사가 실패하면 메서드는 `serializers.ValidationError`(오류)를 발생시켜야합니다. 일반적으로 여기에 있는 `errors` 인수는 필드 이름을 오류 메세지에 매핑하는 dict입니다.  
이 메소드에 전달 된 `data`인수는 일반적으로 `request.data`의 값이므로, 제공하는 데이터 유형은 API에 대해 구성한 파서 클래스에 따라 다릅니다.

### Serializer Inheritance (상속)
Django 폼과 마찬가지로 상속을 통해 serializer를 확장하고 다시 사용할 수 있습니다.
이를 통해 많은 수의 serializer에서 사용할 수 있는 부모 클래스의 공통 필드 또는 메서드 집합을 선언 할 수 있습니다. 예를 들면:

```python
class MyBaseSerializer(Serializer):
    my_field = serializers.CharField()

    def validate_my_field(self):
        ...

class MySerializer(MyBaseSerializer):
    ...
```
Django의 `Model`과 `ModelForm` 클래스처럼, serializer의 내부 `Meta` 클래스는 부모의 내부 `Meta` 클래스를 상속받지 않습니다. `Meta`클래스가 부모 클래스에서 상속 받기를 원한다면 명시해야합니다. 예:

```python
class AccountSerializer(MyBaseSerializer):
    class Meta(MyBaseSerializer.Meta):
        model = Account
```
일반적으로 내부 메타 클래스에서는 상속을 사용하지 않고 모든 옵션을 명시적으로 선언하는 것이 좋습니다.  
또한 다음과 같은 주의사항이 serializer 상속에 적용됩니다.

- 일반적인 Python 이름 해석 규칙이 적용됩니다. `Meta` 내부 클래스를 선언하는 여러 기본 클래스가 있는 경우, 첫번째 클래스만 사용됩니다. 이것은 자녀의 메타가 존재한다면 메타를 의미하고, 그렇지 않으면 첫번째 부모의 메타를 의미합니다.
- 하위 클래스에서 이름을 없음으로 설정하여 부모 클래스에서 상속 된 `Field`를 선언으로 제거 할 수 있습니다.

```python
class MyBaseSerializer(ModelSerializer):
    my_field = serializers.CharField()

class MySerializer(MyBaseSerializer):
    my_field = None
```
그러나 이 방법을 사용하는 경우에만 상위 클래스에 의해 선언적으로 정의 된 필드에서 선택 해재 할 수 있습니다 `ModelSerializer`가 디폴트 필드를 생성하는 것을 막지는 않습니다.기본 필드에서 선택해제하려면 [Specifying which fields to include](http://www.django-rest-framework.org/api-guide/serializers/#specifying-which-fields-to-include)를 참조하세요.

### Dynamically modifying fields (동적으로 필드를 수정)
serializer가 초기화되면 serializer에서 설정된 필드 dict에 `.fields`특성을 사용하여 액서스 할 수 있습니다. 이 속성에 액서스하고 수정하면 serializer 컨버터를 동적으로 수정할 수 있습니다.  
`fields`인수를 직접 수정하면 serializer 선언 시점이 아닌 런타임시 serializer 필드의 인수 변경과 같은 흥미로운 작업을 수행 할 수 있습니다.

#### Example
예를 들어, serializer에서 초기화할 때 사용할 필드를 설정하려면 다음과 같이 serializer 클래스를 만들 수 있습니다.

```python
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
```
이렇게 하면 다음을 수행 할 수 있습니다.

```python
>>> class UserSerializer(DynamicFieldsModelSerializer):
>>>     class Meta:
>>>         model = User
>>>         fields = ('id', 'username', 'email')
>>>
>>> print UserSerializer(user)
{'id': 2, 'username': 'jonwatts', 'email': 'jon@example.com'}
>>>
>>> print UserSerializer(user, fields=('id', 'email'))
{'id': 2, 'email': 'jon@example.com'}
```

### Customizing the default fields
REST 프레임워크2에서는 개발자가 `ModelSerializer`클래스가 기본 필드 set을 자동으로 생성하는 방법을 재정의 할 수 있는 API를 제공했습니다.  
이 API에는 `.get_field()`, `get_pk_field()`와 그외의 메소드가 포함되어 있습니다.  
하지만 serializer가 근본적으로 3.0으로 다시 디자인 되었기 때문에 이 API는 더이상 존재하지 않습니다. 생성 된 필드는 여전히 수정할 수 있지만 소스코드를 참조해야하며, 변경사항이 API의 비공개 비트에 해당하면 변경 될 수 있음을 알고 있어야 합니다.

## Third party packages
다음의 타사 패키지도 제공됩니다.

### Django REST marshmallow
[`Django-rest-marshmallow`](http://www.tomchristie.com/django-rest-marshmallow/) 패키지는 파이썬 [`marshmallow`](https://marshmallow.readthedocs.io/en/latest/) 라이브러리를 사용하여 시리얼라이저의 대체 구현을 제공합니다. REST 프레임워크 serializers와 동일한 API를 제공하며, 일부 use-cases는 drop-in 대체로 사용할 수 있습니다.

### Serpy
[Serpy](https://github.com/clarkduvall/serpy) 패키지는 속도 향상을 위해 만들어진 serializer의 대안 구현입니다. Serpy은 복잡한 데이터 유형을 단순한 기본 유형으로 serializer합니다. 기본 유형은 JSON 이나 필요한 다른 형식으로 쉽게 변환 할 수 있습니다.

### MongoengineModelSerializer
[`django-rest-framework-mongoengine`](https://github.com/umutbozkurt/django-rest-framework-mongoengine)패키지는 `MongiEngineModelSerializer` serializer 클래스를 제공하여 MongoDB를 Django REST 프레임워크의 저장소 계층으로 사용할 수 있도록 지원합니다.

### GeoFeatureModelSerializer
[`django-rest-framework-gis`](https://github.com/djangonauts/django-rest-framework-gis) 패키지는 GeoJSON을 읽기와 쓰기 작업 모두 지원하는 `GeoFeatureModelSerializer` Serializer 클래스를 제공합니다.

### HStoreSerializer
[`django-rest-framework-hstore`](https://github.com/djangonauts/django-rest-framework-hstore)패키지는 [django-hstore](https://github.com/djangonauts/django-hstore) `DictionaryField` 모델 필드와 `schema-mode`기능을 지원하는 `HStoreSerializer`를 제공합니다.
### Dynamic REST
[`Dynamic-Rest`](https://github.com/AltSchool/dynamic-rest) 패키지는 ModelSerializer 및 ModelViewSet 인터페이스를 확장하고 필터링, 정렬, serializer에서 정의한 모든 필드와 관계를 포함/제외하는 API 쿼리 parameter를 추가합니다.

### Dynamic Fields Mixin
[`drf_dynamic-fields`](https://github.com/dbrgn/drf-dynamic-fields) 패키지는 serializer당 필드를 URL parameter로 지정된 서브 세트로 동적으로 제한하기 위해 mixin을 제공합니다.
### DRF FlexFields
[`drf-flex-fields`](https://github.com/rsinger86/drf-flex-fields) 패키지는 ModelSerializer 및 ModelViewSet을 확장하여 필드를 동적으로 설정하고 기본 필드를 중첩 모델로 확장하는데, 일반적으로 사용되는 기능을 URL parameter 및 serializer 클래스 정의에서 모두 제공합니다.

### Serializer Extensions
[`django-rest-framework-serializer-extensions`](https://github.com/evenicoulddoit/django-rest-framework-serializer-extensions) 패키지는 보기/요청 단위로 필드를 정의 할 수있게 하여 serializer를 DRY 할 수 있는 도구 모음을 제공합니다. 필드를 허용 목록에 추가하고 블랙리스트에 올릴 수 있으며 자식 serializer를 선택적으로 확장 할 수 있습니다.

### HTML JSON Forms
[`html-json-forms`](https://github.com/wq/html-json-forms) 패키지는 [`HTML JSON Form specification`](https://www.w3.org/TR/html-json-forms/)(비활성)에 따라 `<form>` 제출을 처리하는 알고리즘 및 serializer를 제공합니다. serializer는 HTML 내에서 임의로 중첩 된 JSON 구조를 쉽게 처리합니다. 예를 들어, `<input name="item[0][id]" value="5">`는 `{"items": [{"id": "5"}]}`으로 해석됩니다.

### DRF-Base64
[`DRF-Base64`](https://bitbucket.org/levit_scs/drf_base64)는  base64 인코딩 파일을 업로드를 처리하는 일련의 필드와 model serializers를 제공합니다.

### QueryFields
[`djangorestframework-queryfields`](http://djangorestframework-queryfields.readthedocs.io/en/latest/)를 사용하면 API 클라이언트가 포함/제외 검색어 parameter를 통해 응답에서 어떤 필드를 보낼지 지정할 수 있습니다.

### DRF Writable Nested
[`drf-writable-nested`](https://github.com/Brogency/drf-writable-nested) 패키지는 중첩 된 관련 데이터로 모델을 작성/업데이트 할 수 있는 쓰기 가능한 중첩 model serializer를 제공합니다.
