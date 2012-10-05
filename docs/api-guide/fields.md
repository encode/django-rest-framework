<a class="github" href="fields.py"></a>

# Serializer fields

> Flat is better than nested.
>
> &mdash; [The Zen of Python][cite]

Serializer fields handle converting between primative values and internal datatypes.  They also deal with validating input values, as well as retrieving and setting the values from their parent objects.

---

**Note:** The serializer fields are declared in fields.py, but by convention you should import them using `from rest_framework import serializers` and refer to fields as `serializers.<FieldName>`.

---

# Generic Fields

## Field

A generic, read-only field.  You can use this field for any attribute that does not need to support write operations.

## WritableField

A field that supports both read and 

## ModelField

A generic field that can be tied to any arbitrary model field.  The `ModelField` class delegates the task of serialization/deserialization to it's associated model field.  This field can be used to create serializer fields for custom model fields, without having to create a new custom serializer field.

**Signature:** `ModelField(model_field=<Django ModelField class>)`

# Typed Fields

These fields represent basic datatypes, and support both reading and writing values.

## BooleanField

## CharField

## EmailField

## DateField

## DateTimeField

## IntegerField

## FloatField

# Relational Fields

Relational fields are used to represent model relationships.  They can be applied to `ForeignKey`, `ManyToManyField` and `OneToOneField` relationships, as well as to reverse relationships, and custom relationships such as `GenericForeignKey`.

## PrimaryKeyRelatedField

## ManyPrimaryKeyRelatedField

## HyperlinkedRelatedField

## ManyHyperlinkedRelatedField

## HyperLinkedIdentityField

[cite]: http://www.python.org/dev/peps/pep-0020/
