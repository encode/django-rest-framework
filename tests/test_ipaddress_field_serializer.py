from django.db import models
from django.test import TestCase

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


# Define the model
class TestModel(models.Model):
    address = models.GenericIPAddressField(protocol="both")

    class Meta:
        app_label = "main"


class TestSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestModel
        fields = "__all__"


# Define the serializer in setUp
class TestSerializerTestCase(TestCase):
    def setUp(self):
        """Initialize serializer class."""
        self.serializer_class = TestSerializer

    def test_invalid_ipv4_for_ipv4_field(self):
        """Test that an invalid IPv4 raises only an IPv4-related error."""
        TestModel._meta.get_field("address").protocol = "IPv4"  # Set field to IPv4 only
        invalid_data = {"address": "invalid-ip"}
        serializer = self.serializer_class(data=invalid_data)

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertEqual(
            str(context.exception.detail["address"][0]),
            "Enter a valid IPv4 address."
        )

    def test_invalid_ipv6_for_ipv6_field(self):
        """Test that an invalid IPv6 raises only an IPv6-related error."""
        TestModel._meta.get_field("address").protocol = "IPv6"  # Set field to IPv6 only
        invalid_data = {"address": "invalid-ip"}
        serializer = self.serializer_class(data=invalid_data)

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertEqual(
            str(context.exception.detail["address"][0]),
            "Enter a valid IPv6 address."
        )

    def test_invalid_both_protocol(self):
        """Test that an invalid IP raises a combined error message when protocol is both."""
        TestModel._meta.get_field("address").protocol = "both"  # Allow both IPv4 & IPv6
        invalid_data = {"address": "invalid-ip"}
        serializer = self.serializer_class(data=invalid_data)

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertEqual(
            str(context.exception.detail["address"][0]),
            "Enter a valid IPv4 or IPv6 address."
        )

    def test_valid_ipv4(self):
        """Test that a valid IPv4 passes validation."""
        TestModel._meta.get_field("address").protocol = "IPv4"
        valid_data = {"address": "192.168.1.1"}
        serializer = self.serializer_class(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_valid_ipv6(self):
        """Test that a valid IPv6 passes validation."""
        TestModel._meta.get_field("address").protocol = "IPv6"
        valid_data = {"address": "2001:db8::ff00:42:8329"}
        serializer = self.serializer_class(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_valid_ipv4_for_both_protocol(self):
        """Test that a valid IPv4 is accepted when protocol is 'both'."""
        TestModel._meta.get_field("address").protocol = "both"
        valid_data = {"address": "192.168.1.1"}
        serializer = self.serializer_class(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_valid_ipv6_for_both_protocol(self):
        """Test that a valid IPv6 is accepted when protocol is 'both'."""
        TestModel._meta.get_field("address").protocol = "both"
        valid_data = {"address": "2001:db8::ff00:42:8329"}
        serializer = self.serializer_class(data=valid_data)
        self.assertTrue(serializer.is_valid())
