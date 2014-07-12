from django.test import TestCase

from rest_framework import serializers
from rest_framework.tests.models import PostalCode, Address, TimeZone


class AddressSerializer(serializers.ModelSerializer):
    postal_code = serializers.MultiSlugRelatedField(
        slug_fields=('code', 'country'),
    )

    class Meta:
        model = Address
        fields = ('id', 'postal_code',)


class TimeZoneSerializer(serializers.ModelSerializer):
    postal_codes = serializers.MultiSlugRelatedField(
        many=True, slug_fields=('code', 'country'),
    )

    class Meta:
        model = TimeZone
        fields = ('id', 'postal_codes',)


class MultiSlugFieldTest(TestCase):
    def test_many_serialization(self):
        postal_code = PostalCode.objects.create(code='12345', country='USA')

        address_a = Address.objects.create(postal_code=postal_code)
        address_b = Address.objects.create(postal_code=postal_code)

        queryset = Address.objects.all()
        serializer = AddressSerializer(queryset, many=True)

        expected = [
            {'id': address_a.pk, 'postal_code': {'code': '12345', 'country': 'USA'}},
            {'id': address_b.pk, 'postal_code': {'code': '12345', 'country': 'USA'}},
        ]
        self.assertEqual(
            serializer.data,
            expected,
        )

    def test_singular_serialization(self):
        postal_code = PostalCode.objects.create(code='12345', country='USA')
        address = Address.objects.create(postal_code=postal_code)

        serializer = AddressSerializer(address)

        expected = {
            'id': address.pk,
            'postal_code': {
                'code': postal_code.code,
                'country': postal_code.country,
            },
        }
        self.assertEqual(
            serializer.data,
            expected,
        )

    def test_singular_serialization_when_null(self):
        address = Address.objects.create()

        serializer = AddressSerializer(address)

        expected = {
            'id': address.pk,
            'postal_code': None,
        }
        self.assertEqual(
            serializer.data,
            expected,
        )

    def test_foreign_key_creation(self):
        postal_code = PostalCode.objects.create(code='12345', country='USA')

        serializer = AddressSerializer(data={
            'postal_code': {
                'code': postal_code.code,
                'country': postal_code.country,
            },
        })
        self.assertTrue(serializer.is_valid())
        address = serializer.save()
        self.assertEqual(address.postal_code, postal_code)

    def test_foreign_key_update(self):
        postal_code = PostalCode.objects.create(code='12345', country='USA')
        address = Address.objects.create(postal_code=postal_code)

        new_postal_code = PostalCode.objects.create(code='54321', country='USA')

        serializer = AddressSerializer(data={
            'postal_code': {
                'code': new_postal_code.code,
                'country': new_postal_code.country,
            },
        })
        self.assertTrue(serializer.is_valid())
        address = serializer.save()
        self.assertEqual(address.postal_code, new_postal_code)

    def test_foreign_key_update_incomplete_slug(self):
        postal_code = PostalCode.objects.create(code='12345', country='USA')

        serializer = AddressSerializer(data={
            'postal_code': {
                'code': postal_code.code,
            },
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('postal_code', serializer.errors)

    def test_foreign_key_update_incorrect_type(self):
        serializer = AddressSerializer(data={
            'postal_code': 1234,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('postal_code', serializer.errors)

    def test_reverse_foreign_key_retrieve(self):
        timezone = TimeZone.objects.create()
        PostalCode.objects.create(code='12345', country='USA', timezone=timezone)
        PostalCode.objects.create(code='54321', country='USA', timezone=timezone)

        serializer = TimeZoneSerializer(timezone)

        expected = {
            'id': timezone.pk,
            'postal_codes': [
                {'code': '12345', 'country': 'USA'},
                {'code': '54321', 'country': 'USA'},
            ]
        }
        self.assertEqual(
            serializer.data,
            expected,
        )

    def test_reverse_foreign_key_create(self):
        PostalCode.objects.create(code='12345', country='USA')
        PostalCode.objects.create(code='54321', country='USA')
        data = {
            'postal_codes': [
                {'code': '12345', 'country': 'USA'},
                {'code': '54321', 'country': 'USA'},
            ]
        }

        serializer = TimeZoneSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        new_timezone = serializer.save()

        self.assertEqual(new_timezone.postal_codes.count(), 2)

        self.assertTrue(
            PostalCode.objects.filter(
                code='12345', country='USA', timezone=new_timezone,
            ).exists(),
        )
        self.assertTrue(
            PostalCode.objects.filter(
                code='54321', country='USA', timezone=new_timezone,
            ).exists(),
        )

    def test_reverse_foreign_key_update(self):
        timezone = TimeZone.objects.create()
        PostalCode.objects.create(code='12345', country='USA')
        PostalCode.objects.create(code='54321', country='USA')

        data = {
            'id': timezone.pk,
            'postal_codes': [
                {'code': '12345', 'country': 'USA'},
                {'code': '54321', 'country': 'USA'},
            ]
        }

        # There should be no postal codes
        self.assertEqual(timezone.postal_codes.count(), 0)

        serializer = TimeZoneSerializer(timezone, data=data)

        self.assertTrue(serializer.is_valid())

        updated_timezone = serializer.save()

        self.assertEqual(updated_timezone.postal_codes.count(), 2)
