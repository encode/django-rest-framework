"""
Helper classes for parsers.
"""
from __future__ import unicode_literals
from django.utils import timezone
from django.db.models.query import QuerySet
from django.utils.datastructures import SortedDict
from django.utils.functional import Promise
from rest_framework.compat import force_text
import datetime
import decimal
import types
import json


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time/timedelta,
    decimal types, generators and other basic python objects.
    """
    def default(self, obj):
        # For Date Time string spec, see ECMA 262
        # http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(obj, Promise):
            return force_text(obj)
        elif isinstance(obj, datetime.datetime):
            representation = obj.isoformat()
            if obj.microsecond:
                representation = representation[:23] + representation[26:]
            if representation.endswith('+00:00'):
                representation = representation[:-6] + 'Z'
            return representation
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            if timezone and timezone.is_aware(obj):
                raise ValueError("JSON can't represent timezone-aware times.")
            representation = obj.isoformat()
            if obj.microsecond:
                representation = representation[:12]
            return representation
        elif isinstance(obj, datetime.timedelta):
            return str(obj.total_seconds())
        elif isinstance(obj, decimal.Decimal):
            # Serializers will coerce decimals to strings by default.
            return float(obj)
        elif isinstance(obj, QuerySet):
            return list(obj)
        elif hasattr(obj, 'tolist'):
            # Numpy arrays and array scalars.
            return obj.tolist()
        elif hasattr(obj, '__getitem__'):
            try:
                return dict(obj)
            except:
                pass
        elif hasattr(obj, '__iter__'):
            return [item for item in obj]
        return super(JSONEncoder, self).default(obj)


try:
    import yaml
except ImportError:
    SafeDumper = None
else:
    # Adapted from http://pyyaml.org/attachment/ticket/161/use_ordered_dict.py
    class SafeDumper(yaml.SafeDumper):
        """
        Handles decimals as strings.
        Handles SortedDicts as usual dicts, but preserves field order, rather
        than the usual behaviour of sorting the keys.
        """
        def represent_decimal(self, data):
            return self.represent_scalar('tag:yaml.org,2002:str', str(data))

        def represent_mapping(self, tag, mapping, flow_style=None):
            value = []
            node = yaml.MappingNode(tag, value, flow_style=flow_style)
            if self.alias_key is not None:
                self.represented_objects[self.alias_key] = node
            best_style = True
            if hasattr(mapping, 'items'):
                mapping = list(mapping.items())
                if not isinstance(mapping, SortedDict):
                    mapping.sort()
            for item_key, item_value in mapping:
                node_key = self.represent_data(item_key)
                node_value = self.represent_data(item_value)
                if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
                    best_style = False
                if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
                    best_style = False
                value.append((node_key, node_value))
            if flow_style is None:
                if self.default_flow_style is not None:
                    node.flow_style = self.default_flow_style
                else:
                    node.flow_style = best_style
            return node

    SafeDumper.add_representer(
        decimal.Decimal,
        SafeDumper.represent_decimal
    )
    SafeDumper.add_representer(
        SortedDict,
        yaml.representer.SafeRepresenter.represent_dict
    )
    # SafeDumper.add_representer(
    #     DictWithMetadata,
    #     yaml.representer.SafeRepresenter.represent_dict
    # )
    # SafeDumper.add_representer(
    #     SortedDictWithMetadata,
    #     yaml.representer.SafeRepresenter.represent_dict
    # )
    SafeDumper.add_representer(
        types.GeneratorType,
        yaml.representer.SafeRepresenter.represent_list
    )
