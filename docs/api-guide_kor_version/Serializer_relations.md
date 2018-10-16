# Django REST framework - Serializer relations

---

_"Bad programmers worry about the code. Good programmers worry about data structures and their relationships."_  

_"나쁜 프로그래머는 코드에 대해 걱정합니다. 좋은 프로그래머는 데이터 구조와 그 관계에 대해 걱정합니다."_  

_— Linus Torvalds_

---

## Serializer relations
relational field는 모델 관계를 나타내는데 사용됩니다. `ForeignKey`, `ManyToManyField` 및 `OneToOneField` 관계는 물론 관계 및  custom 관계 (예 : `GenericForeignKey`)를 역으로 적용 할 수 있습니다.

---

**Note**: 관계형 필드는 `relations.py`에 선언되어 있지만, 관습에 따라 `serializer` 모듈에서 가져와야하며, `rest_framework import serializer`에서 사용하고 `serializer.<FiledName>` 로 필드를 참조해야합니다.

---

### Inspecting relationships.
`ModelSerializer` 클래스를 사용하면 serializer 필드와 관계가 자동으로 생성됩니다. 이러한 자동 생성 필드를 검사하는 것은 관계 스타일을 custom하는 방법을 결정하는데 유용한 도구가 될 수 있습니다.  
이렇게 하려면, Django의 쉘을 열고, `python manage.py shell`을 사용하고, serializer 클래스를 가져와서 인스턴스화하고, 객체 표현을 출력하세요.

```python
>>> from myapp.serializers import AccountSerializer
>>> serializer = AccountSerializer()
>>> print repr(serializer)  # Or `print(repr(serializer))` in Python 3.x.
AccountSerializer():
    id = IntegerField(label='ID', read_only=True)
    name = CharField(allow_blank=True, max_length=100, required=False)
    owner = PrimaryKeyRelatedField(queryset=User.objects.all())
```

## API Reference
다양한 유형의 관계 필드를 설명하기 위해 예제에 몇가지 간단한 모델을 사용합니다. 우리 모델은 음악 앨범과 각 앨범에 수록된 트랙을 대상으로 합니다.  

```python
class Album(models.Model):
    album_name = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)

class Track(models.Model):
    album = models.ForeignKey(Album, related_name='tracks', on_delete=models.CASCADE)
    order = models.IntegerField()
    title = models.CharField(max_length=100)
    duration = models.IntegerField()

    class Meta:
        unique_together = ('album', 'order')
        ordering = ['order']

    def __unicode__(self):
        return '%d: %s' % (self.order, self.title)
```

### StringRelatedField
`StringRelatedField`는 `__unicode__`메서드를 사용하여 관계의 대상을 나타내는데 사용할 수 있습니다.  
예를 들어 다음 serializer와 같습니다.

```python
class AlbumSerializer(serializers.ModelSerializer):
    tracks = serializers.StringRelatedField(many=True)

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'tracks')
```
다음과 같은 표현으로 serializer합니다.

```python
{
    'album_name': 'Things We Lost In The Fire',
    'artist': 'Low',
    'tracks': [
        '1: Sunflower',
        '2: Whitetail',
        '3: Dinosaur Act',
        ...
    ]
}
```
이 필드는 읽기 전용입니다.  

**Arguments**:  

- `many` : to-many 관계에 적용되면 이 인수는 `True`로 설정해야합니다.

### PrimaryKeyRelatedField
`primaryKeyRelatedField`는 primary key를 사용하여 관계의 대상을 나타내는데 사용할 수 있습니다.  
예를 들어 다음 serializer가 있습니다.

```python
class AlbumSerializer(serializers.ModelSerializer):
    tracks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'tracks')
```
다음과 같이 표현할 수 있습니다.

```python
{
    'album_name': 'Undun',
    'artist': 'The Roots',
    'tracks': [
        89,
        90,
        91,
        ...
    ]
}
```
기본적으로 이 필드는 읽기전용이지만, `read_only`플래그를 사용하여 이 동작을 변경할 수 있습니다.  

**Arguments**:  

- `queryset` : 필드 입력의 유효성을 검사 할 때 모델 인스턴스 조회에 사용되는 쿼리 세트입니다. 관계는 명시적으로 쿼리 세트를 설정하거나 `read_only=True`로 설정해야합니다.
- `many` : to-many 관계에 적용되면이 인수를 `True`로 설정해야합니다.
- `allow_null` : `True`로 설정하면 필드에 `None` 값 또는 null 허용 관계에 대한 빈 문자열을 허용합니다. 기본값은 `False`입니다.
- `pk_field` : primary key 값의 serialzier/deserializer를 제어하는 ​​필드로 설정합니다. 예를 들어 ₩pk_field=UUIDField(format='hex')₩는 UUID primary key를 컴팩트 16 진수 표현으로 serializer화합니다.

### HyperlinkedRelatedField
`HyperlinkedRelatedField`는 하이퍼링크를 사용하여 관계의 대상을 나타내는데 사용할 수 있습니다.  
예를 들어 다음 serializer가 있습니다.

```python
class AlbumSerializer(serializers.ModelSerializer):
    tracks = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='track-detail'
    )

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'tracks')
```
다음과 같이 표현할 수 있습니다.

```python
{
    'album_name': 'Graceland',
    'artist': 'Paul Simon',
    'tracks': [
        'http://www.example.com/api/tracks/45/',
        'http://www.example.com/api/tracks/46/',
        'http://www.example.com/api/tracks/47/',
        ...
    ]
}
```
기본적으로 이 필드는 읽기전용이지만, `read_only`플래그를 사용하여 이 동작을 변경할 수 있습니다.

---

**Note**: 이 필드는 `lookup_field` 및 `lookup_url_kwarg` 인수를 사용하여 설정된대로 단일 URL 키워드 인수를 허용하는 URL에 매핑되는 개체를 위해 설계되었습니다.  
URL의 일부로 단일 primary key 또는 slug 인수가 포함된 URL에 적합힙니다.  
보다 복잡한 하이퍼 링크로 표현이 필요한 경우에는 아래의 [custom hyperlinked field](http://www.django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields)섹션에 설명 된대로 custom해야 합니다.

---

**Arguments**:  

- `view_name` : 관계의 대상으로 사용해야하는 view 이름입니다. [표준 라우터 클래스]()를 사용하는 경우 `<modelname>-detail` 형식의 문자열이 됩니다. **필수.**
- `queryset` : 필드 입력의 유효성을 검사 할 때 모델 인스턴스 조회에 사용되는 쿼리셋입니다. 관계는 명시적으로 쿼리셋을 설정하거나 `read_only=True`로 설정해야합니다.
- `many` - to-many 관계에 적용되면 이 인수를 `True`로 설정해야합니다.
- `allow_null` : `True`로 설정하면 필드에 `None` 값 또는 null 허용 관계에 대한 빈 문자열을 허용합니다. 기본값은 `False`입니다.
- `lookup_field` : 조회에 사용해야하는 대상의 필드입니다. 참조 된 뷰의 URL 키워드 인수에 해당해야합니다. 기본값은 `pk`입니다.
- `lookup_url_kwarg` : 조회 필드에 해당하는 URL conf에 정의된 키워드 인수의 이름입니다. 기본적으로 `lookup_field`와 같은 값을 사용합니다.
- `format` : format suffix를 사용하는 경우, 하이퍼 링크 된 필드는 `format`인수를 사용하여 오버라이드하지 않는 한 대상에 대해 동일한 format suffix를 사용합니다.

### SlugRelatedField
`slugRelatedField`는 대상 필드를 사용하여 관계 대상을 나타내는데 사용할 수 있습니다.  
예를 들어 다음 serializer가 있습니다.

```python
class AlbumSerializer(serializers.ModelSerializer):
    tracks = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='title'
     )

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'tracks')
```
다음과 같이 표현할 수 있습니다.

```python
{
    'album_name': 'Dear John',
    'artist': 'Loney Dear',
    'tracks': [
        'Airport Surroundings',
        'Everything Turns to You',
        'I Was Only Going Out',
        ...
    ]
}
```
기본적으로 이 필드는 읽기 전용이지만, `read_only`플래그를 사용하여 이 동작을 변경할 수 있습니다.  
`SlugRelatedField`를 read-write 필드로 사용할 때는 일반적으로 slug 필드가 `unique=True`인 모델 필드에 해당하는지 확인해야합니다.  

**Arguments**:  

- `slug_field` : 그것을 나타내는데 사용해야하는 대상의 필드입니다. 주어진 인스턴스를 고유하게 식별하는 필드이어야 합니다. 예: `username`. **필수**
- `queryset` : 필드 입력의 유효성을 검사 할 때 모델 인스턴스 조회에 사용되는 쿼리셋입니다. 관계는 명시적으로 쿼리셋을 설정하거나 `read_only=True`로 설정해야 합니다.
- `many` : to-many 관계에 적용되면 이 인수를 `True`로 설정해야합니다.
- `allow_null` : `True`로 설정하면 필드에 `None` 값 또는 null 허용 관계에 대한 빈 문자열을 허용합니다. 기본값은 `False`입니다.

### HyperlinkedIdentityField
이 필드는 `HyperlinkedModelSerializer`의 `url`필드와 같은 동일한 관계로 적용될 수 있습니다. 객체의 속성에도 사용할 수 있습니다. 예를 들어, 다음 serializer가 있습니다.  

```python
class AlbumSerializer(serializers.HyperlinkedModelSerializer):
    track_listing = serializers.HyperlinkedIdentityField(view_name='track-list')

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'track_listing')
```
다음과 같이 표현할 수 있습니다.

```python
{
    'album_name': 'The Eraser',
    'artist': 'Thom Yorke',
    'track_listing': 'http://www.example.com/api/track_list/12/',
}
```
이 필드는 항상 읽기 전용입니다.  

**Arguments**:  

- `view_name` : 관계의 대상으로 사용해야하는 view 이름입니다. 표준 라우터 클래스를 사용하는 경우 `<model_name>-detail` 형식의 문자열이 됩니다. **필수**
- `lookup_field` : 조회에 사용해야하는 대상의 필드입니다. 참조 된 뷰의 URL 키워드 인수에 해당해야합니다. 기본값은 `'pk'`입니다.
- `lookup_url_kwarg` : 조회 필드에 해당하는 URL conf에 정의 된 키워드 인수의 이름입니다. 기본적으로 `lookup_field`와 같은 값을 사용합니다.
- `format` -  format suffix를 사용하는 경우 하이퍼 링크 된 필드는 `format` 인수를 사용하여  오버라이드하지 않는한 대상에 대해 동일한  format suffix를 사용합니다.

---

## Nested relationships
중첩 된 관계는 serializer를 필드로 사용하여 표현할 수 있습니다.  
필드가 to-many 관계를 나타내는데 사용되는 경우 serializer필드에 `many=True`플래그를 추가해야합니다.  

### Example
예를 들어 다음 serializer가 있습니다.

```python
class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ('order', 'title', 'duration')

class AlbumSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True, read_only=True)

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'tracks')
```
다음과 같이 중첩된 표현으로 serializer 합니다.

```python
>>> album = Album.objects.create(album_name="The Grey Album", artist='Danger Mouse')
>>> Track.objects.create(album=album, order=1, title='Public Service Announcement', duration=245)
<Track: Track object>
>>> Track.objects.create(album=album, order=2, title='What More Can I Say', duration=264)
<Track: Track object>
>>> Track.objects.create(album=album, order=3, title='Encore', duration=159)
<Track: Track object>
>>> serializer = AlbumSerializer(instance=album)
>>> serializer.data
{
    'album_name': 'The Grey Album',
    'artist': 'Danger Mouse',
    'tracks': [
        {'order': 1, 'title': 'Public Service Announcement', 'duration': 245},
        {'order': 2, 'title': 'What More Can I Say', 'duration': 264},
        {'order': 3, 'title': 'Encore', 'duration': 159},
        ...
    ],
}
```

### Writable nested serializers
기본적으로 nested serializer는 읽기 전용입니다. 중첩 된 serializer 필드에 대한 쓰기 작업을 지원하려면 `creat()`와 `/`또는 `update()`메서드를 만들어 자식 관계를 저장하는 방법을 명시적으로 지정해야합니다.

```python
class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ('order', 'title', 'duration')

class AlbumSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True)

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'tracks')

    def create(self, validated_data):
        tracks_data = validated_data.pop('tracks')
        album = Album.objects.create(**validated_data)
        for track_data in tracks_data:
            Track.objects.create(album=album, **track_data)
        return album

>>> data = {
    'album_name': 'The Grey Album',
    'artist': 'Danger Mouse',
    'tracks': [
        {'order': 1, 'title': 'Public Service Announcement', 'duration': 245},
        {'order': 2, 'title': 'What More Can I Say', 'duration': 264},
        {'order': 3, 'title': 'Encore', 'duration': 159},
    ],
}
>>> serializer = AlbumSerializer(data=data)
>>> serializer.is_valid()
True
>>> serializer.save()
<Album: Album object>
```

---

## Custom relational fields
기존의 관계형 스타일이 필요하지 않은 경우가 드물지만 모델 인스턴스에서 출력 표현을 생성하는 방법을 정확하게 설명하는 완벽한 custom relational field를 구현할 수 있습니다.  
custom relational field를 구현하려면 RelatedField를 오버라이드하고 `.to_representation(self, value)` 메서드를 구현해야합니다. 이 메서드는 필드의 대상을 `value`인수로 사용하고 대상을 serializer하는데 사용해야하는 표현을 반환해야합니다. `value`인수는 일반적으로 모델 인스턴스입니다.  
 read-write relational field를 구현하려면 `.to_internal_value(self, data)` 메소드도 구현해야합니다.  
contextd를 기반으로 동적 쿼리셋을 제공하려면 클래스에서 `.queryset`을 지정하거나 필드를 초기화 할 때 `.get_queryset(self)`를 오버라이드 할 수도 있습니다.

### Example
예를 들어, 순서, 제목, 기간을 사용하여 트랙을 custom 문자열 표현으로 serializer하는 relational field를 정의할 수 있습니다.

```python
import time

class TrackListingField(serializers.RelatedField):
    def to_representation(self, value):
        duration = time.strftime('%M:%S', time.gmtime(value.duration))
        return 'Track %d: %s (%s)' % (value.order, value.name, duration)

class AlbumSerializer(serializers.ModelSerializer):
    tracks = TrackListingField(many=True)

    class Meta:
        model = Album
        fields = ('album_name', 'artist', 'tracks')
```
이 custom 필드는 다음 표현으로 serializer 됩니다.

```python
{
    'album_name': 'Sometimes I Wish We Were an Eagle',
    'artist': 'Bill Callahan',
    'tracks': [
        'Track 1: Jim Cain (04:39)',
        'Track 2: Eid Ma Clack Shaw (04:19)',
        'Track 3: The Wind and the Dove (04:34)',
        ...
    ]
}
```

---

## Custom hyperlinked fields
어떤 경우에는 하나 이상의 조회 필드가 필요한 URL을 나타내기 위해 하이퍼링크 필드의 동작을 custom 해야 할 수도 있습니다.  
`HyperlinkedRelatedField`를 오버라이드 하여 이 작업을 수행 할 수 있습니다. 오버라이드 할 수 있는 두 가지 방법이 있습니다.  

#### get_url(self, obj, view_name, request, format)
`get_url` 메서드는 객체 인스턴스를 URL 표현에 매핑하는 데 사용됩니다.  
`view_name` 및 `lookup_field` 속성이 URL conf와 정확하게 일치하도록 구성되지 않은 경우 `NoReverseMatch`를 발생시킬 수 있습니다.  

#### get_object(self, queryset, view_name, view_args, view_kwargs)
쓰기 가능한 하이퍼링크 필드를 지원하려면 들어오는 URL을 그들이 나타내는 객체로 다시 매핑하기 위해 `get_object`를 오버라이드해야합니다. 읽기 전용 하이퍼링크 필드의 경우 이 메서드를 오버라이드 할 필요가 없습니다.  
이 메서드의 반환 값은 일치하는 URL conf 인수에 해당하는 객체이어야 합니다.  
`ObjectDoesNotExist` 예외가 발생할 수 있습니다.

### Example
다음과 같이 두 개의 키워드 인수를 취하는 고객 객체의 URL이 있다고 가정해보세요.

```
/api/<organization_slug>/customers/<customer_pk>/
```
단일의 lookup field 만을 받아들이는 기본 구현에서는 이것을 표현할 수 없습니다.  
이 경우 우리가 원하는 동작을 얻으려면 `HyperlinkedRelatedField`를 오버라이드해야합니다.

```python
from rest_framework import serializers
from rest_framework.reverse import reverse

class CustomerHyperlink(serializers.HyperlinkedRelatedField):
    # We define these as class attributes, so we don't need to pass them as arguments.
    view_name = 'customer-detail'
    queryset = Customer.objects.all()

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            'organization_slug': obj.organization.slug,
            'customer_pk': obj.pk
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        lookup_kwargs = {
           'organization__slug': view_kwargs['organization_slug'],
           'pk': view_kwargs['customer_pk']
        }
        return self.get_queryset().get(**lookup_kwargs)
```
이 스타일을 generic view 와 함께 사용하려는 경우 올바른 조회 동작을 얻으려면 뷰에서 `.get_object`를 오버라이드 해야합니다.  
일반적으로 가능한 경우 API 표현에 플랫 스타일을 사용하는 것이 좋지만, 중첩된 URL 스타일은 적당히 사용하면 합리적일 수 있습니다.

---

## Further notes

### The `queryset` argument
`queryset`인수는 쓰기 가능한 관계 필드에만 필요합니다. 이 경우 기본 인스턴스 사용자 입력 모델 인스턴스로 매핑되는 모델 인스턴스 조회를 수행하는데 사용됩니다.  
버전 2.x에서는 serializer 클래스가 `ModelSerializer` 클래스가 사용되는 경우 `queryset` 인수를 자동으로 결정할 수 있습니다.  
이 동작은 이제 쓰기 가능한 관계형 필드에 대해 명시적 쿼리셋 인수를 항상 사용하여 대체되었습니다.  
이렇게하면 `ModelSerializer`이 제공하는 숨겨진 'magic'양이 줄어들고 필드의 동작이 더 명확해지며 `ModelSerializer` shortcut를 사용하거나 완전하게 명시적인 `Serializer`클래스를 사용하는 것이 쉽다는 것을 보증합니다.

### Customizing the HTML display
모델의 내장 `__str__`메서드는 `choices`속성을 채우는데 사용 된 객체의 문자열 표현을 생성하는데 사용됩니다. 이러한 선택사항은 탐색 가능한 API에서 선택된 HTML 입력을 채우는데 사용됩니다.  
이러한 입력에 대해 custom 된 표현을 제공하려면 `RelatedField` 서브 클래스의 `display_value()`를 대체하세요. 이 메서드는 모델 객체를 수신하고 모델 객체를 나타내는데 적합한 문자열을 반환해야합니다. 예:

```python
class TrackPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def display_value(self, instance):
        return 'Track: %s' % (instance.title)
```

### Select field cutoffs
browsable API에서 렌더링 될 때 관계형 필드는 기본적으로 최대 1000개의 선택 가능한 항목만 표시합니다. 더 많은 항목이 있으면 "More than 1000 items..."와 함께 비활성화 된 옵션이 표시됩니다.  
이 동작은 매우 많은 수의 관계가 표시되어 허용되는 범위 내에서 템플릿을 렌더링 할 수 없도록 하기 위한 것입니다.  
이 동작을 제어하는데 사용할 수 있는 두 개의 키워드인수가 있습니다.  

- `html_cutoff` : 설정된 경우 HTML 선택 드롭 다운에 표시 될 최대 선택 항목 수입니다. 제한을 해제하려면 `None`으로 설정하십시오. 기본값은 `1000`입니다.
- `html_cutoff_text` - 설정된 경우 HTML 선택 드롭 다운에서 최대 항목 수가 잘린 경우 텍스트 표시를 보여줍니다. 기본값은 `"More than {count} items…"`입니다.  

`HTML_SELECT_CUTOFF` 및 `HTML_SELECT_CUTOFF_TEXT` 설정을 사용하여 전역으로 제어 할 수도 있습니다.  
컷오프가 적용되는 경우 HTML 양식에 일반 입력 필드를 대신 사용할 수 있습니다. `style` 키워드 인수를 사용하면됩니다. 예 :

```python
assigned_to = serializers.SlugRelatedField(
   queryset=User.objects.all(),
   slug_field='username',
   style={'base_template': 'input.html'}
)
```

### Reverse relations
reverse 관계는 `ModelSerializer`및 `HyperlinkedModelSerializer`클래스에 자동으로 포함되지 않습니다. reverse 관계를 포함 시키려면 필드 목록에 명시적으로 추가해야합니다. 예:

```python
class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('tracks', ...)
```
일반적으로 필드 이름으로 사용할 수 있는 적절한 `related_name`인수를 관계에 설정했는지 확인해야합니다. 예:

```python
class Track(models.Model):
    album = models.ForeignKey(Album, related_name='tracks', on_delete=models.CASCADE)
    ...
```
reverse 관계에 대한 관련 이름을 설정하지 않은 경우 `fields`인수에 자동으로 생성 된 관련 이름을 사용해야합니다. 예:

```python
class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('track_set', ...)
```
자세한 내용은 [reverse relationships](https://docs.djangoproject.com/en/1.10/topics/db/queries/#following-relationships-backward)에 대한 Django 문서를 참조하세요.

### Generic relationships
일반적인 foreign key를 serializer하려면 관계의 대상을 serializer화하는 방법을 명시적으로 결정하기 위해 custom 필드를 정의해야합니다.  
예를 들어, 다른 임의의 모델과 일반적인 관계가 있는 태그에 대해 다음 모델이 제공됩니다.

```python
class TaggedItem(models.Model):
    """
    Tags arbitrary model instances using a generic relation.

    See: https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/
    """
    tag_name = models.SlugField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    tagged_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.tag_name
```
그리고 다음 두 모델의 관련 태그를 가질 수 있습니다.

```python
class Bookmark(models.Model):
    """
    A bookmark consists of a URL, and 0 or more descriptive tags.
    """
    url = models.URLField()
    tags = GenericRelation(TaggedItem)


class Note(models.Model):
    """
    A note consists of some text, and 0 or more descriptive tags.
    """
    text = models.CharField(max_length=1000)
    tags = GenericRelation(TaggedItem)
```
태그가 지정된 인스턴스를 serializer하는데 사용할 수 있는 custom 필드를 정의하여 각 인스턴스의 유형을 사용하여 serializer 해야하는 방식을 결정할 수 있습니다.

```python
class TaggedObjectRelatedField(serializers.RelatedField):
    """
    A custom field to use for the `tagged_object` generic relationship.
    """

    def to_representation(self, value):
        """
        Serialize tagged objects to a simple textual representation.
        """
        if isinstance(value, Bookmark):
            return 'Bookmark: ' + value.url
        elif isinstance(value, Note):
            return 'Note: ' + value.text
        raise Exception('Unexpected type of tagged object')
```
관계의 타겟이 중첩 된 표현을 필요로 하는 경우 `.to_representation()`메서드 내에서 필요한 serializer를 사용할 수 있습니다.

```python
  def to_representation(self, value):
        """
        Serialize bookmark instances using a bookmark serializer,
        and note instances using a note serializer.
        """
        if isinstance(value, Bookmark):
            serializer = BookmarkSerializer(value)
        elif isinstance(value, Note):
            serializer = NoteSerializer(value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data
```
`GenericRelation`필드를 사용하여 표현된 reverse generic key는 관계의 대상 유형이 항상 알려져 있으므로 일반 관계형 필드 유형을 사용하여 serializer화 할 수 있습니다.  
더 자세한 정보는 [the Django documentation on generic relations](https://docs.djangoproject.com/en/1.10/ref/contrib/contenttypes/#id1)를 참조하세요.

### ManyToManyFields with a Through Model
기본적으로 지정된 `through` 모델을 사용하여 `ManyToManyField`를 대상으로하는 관계형 필드는 읽기전용으로 설정됩니다.  
through 모델을 사용하여 `manyToManyField`를 가리키는 관계 필드를 명시적으로 지정하면 `read_only`를 `True`로 설정하세요.

---

## Third Party Packages
다음의 타사 패키지도 제공됩니다.

### DRF Nested Routers
[drf-nested-routers](https://github.com/alanjds/drf-nested-routers) 패키지는 중첩 된 리소스로 작업하기 위한 라우터 및 관계 필드를 제공합니다.

### Rest Framework Generic Relations
[rest-framework-generic-relations](https://github.com/Ian-Foote/rest-framework-generic-relations) 라이브러리는 일반적인 foreign key에 대한 read/write serializer화를 제공합니다.
