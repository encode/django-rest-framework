from rest_framework import serializers

from ..base import FieldValues


class TestIPAddressField(FieldValues):
    """
    Valid and invalid values for `IPAddressField`
    """
    valid_inputs = {
        '127.0.0.1': '127.0.0.1',
        '192.168.33.255': '192.168.33.255',
        '2001:0db8:85a3:0042:1000:8a2e:0370:7334': '2001:db8:85a3:42:1000:8a2e:370:7334',
        '2001:cdba:0:0:0:0:3257:9652': '2001:cdba::3257:9652',
        '2001:cdba::3257:9652': '2001:cdba::3257:9652'
    }
    invalid_inputs = {
        '127001': ['Enter a valid IPv4 or IPv6 address.'],
        '127.122.111.2231': ['Enter a valid IPv4 or IPv6 address.'],
        '2001:::9652': ['Enter a valid IPv4 or IPv6 address.'],
        '2001:0db8:85a3:0042:1000:8a2e:0370:73341': ['Enter a valid IPv4 or IPv6 address.'],
        1000: ['Enter a valid IPv4 or IPv6 address.'],
    }
    outputs = {}
    field = serializers.IPAddressField()


class TestIPv4AddressField(FieldValues):
    """
    Valid and invalid values for `IPAddressField`
    """
    valid_inputs = {
        '127.0.0.1': '127.0.0.1',
        '192.168.33.255': '192.168.33.255',
    }
    invalid_inputs = {
        '127001': ['Enter a valid IPv4 address.'],
        '127.122.111.2231': ['Enter a valid IPv4 address.'],
    }
    outputs = {}
    field = serializers.IPAddressField(protocol='IPv4')


class TestIPv6AddressField(FieldValues):
    """
    Valid and invalid values for `IPAddressField`
    """
    valid_inputs = {
        '2001:0db8:85a3:0042:1000:8a2e:0370:7334': '2001:db8:85a3:42:1000:8a2e:370:7334',
        '2001:cdba:0:0:0:0:3257:9652': '2001:cdba::3257:9652',
        '2001:cdba::3257:9652': '2001:cdba::3257:9652'
    }
    invalid_inputs = {
        '2001:::9652': ['Enter a valid IPv4 or IPv6 address.'],
        '2001:0db8:85a3:0042:1000:8a2e:0370:73341': ['Enter a valid IPv4 or IPv6 address.'],
    }
    outputs = {}
    field = serializers.IPAddressField(protocol='IPv6')
