"""
Query analyzer for detecting N+1 query problems in Django REST Framework.

This module provides utilities to analyze serializer fields and detect potential
N+1 query issues before they occur.
"""

import warnings

from django.db import models
from django.db.models import ForeignKey, ManyToManyField, OneToOneField

from rest_framework import serializers
from rest_framework.relations import RelatedField, ManyRelatedField
from rest_framework.utils import model_meta


class QueryAnalyzer:
    """
    Analyzes serializer fields to detect potential N+1 query problems.
    
    This class examines serializer field definitions to identify relationships
    that may cause N+1 queries when serializing querysets.
    """
    
    def __init__(self, serializer_class):
        """
        Initialize the analyzer with a serializer class.
        
        Args:
            serializer_class: The serializer class to analyze
        """
        self.serializer_class = serializer_class
        self._field_analysis = None
    
    def analyze(self):
        """
        Analyze the serializer and return a dictionary with optimization suggestions.
        
        Returns:
            Dictionary containing:
            - select_related: List of fields that should use select_related
            - prefetch_related: List of fields that should use prefetch_related
            - nested_serializers: List of nested serializer fields
        """
        if self._field_analysis is None:
            self._field_analysis = self._analyze_fields()
        return self._field_analysis
    
    def _analyze_fields(self):
        """Analyze serializer fields to identify relationships."""
        analysis = {
            'select_related': [],
            'prefetch_related': [],
            'nested_serializers': [],
            'warnings': []
        }
        
        if not issubclass(self.serializer_class, serializers.ModelSerializer):
            return analysis
        
        # Get the model from the serializer
        model = getattr(self.serializer_class.Meta, 'model', None)
        if not model:
            return analysis
        
        # Get field info using DRF's utility
        try:
            field_info = model_meta.get_field_info(model)
        except Exception:
            return analysis
        
        # Analyze declared fields
        serializer = self.serializer_class()
        fields = serializer.fields
        
        for field_name, field in fields.items():
            # Analyze fields that are readable (not write_only)
            # This includes read_only fields and fields that can be both read and written
            if not field.write_only:
                self._analyze_field(field_name, field, model, field_info, analysis)
        
        return analysis
    
    def _analyze_field(self, field_name, field, model, field_info, analysis):
        """Analyze a single field for potential N+1 issues."""
        source = getattr(field, 'source', field_name)
        source_parts = source.split('.')
        base_field_name = source_parts[0]
        
        # Check if it's a ManyRelatedField (many=True on RelatedField)
        # This handles custom fields like PrimaryKeyRelatedField(many=True)
        if isinstance(field, ManyRelatedField):
            # ManyToMany or reverse relationship - use prefetch_related
            if base_field_name not in analysis['prefetch_related']:
                analysis['prefetch_related'].append(base_field_name)
            return  # Early return since ManyRelatedField is handled
        
        # Check if it's a related field
        if isinstance(field, RelatedField):
            # Check if it's in the model's relationships
            if base_field_name in field_info.relations:
                relation_info = field_info.relations[base_field_name]
                
                if not relation_info.to_many:
                    # ForeignKey or OneToOneField - use select_related
                    if base_field_name not in analysis['select_related']:
                        analysis['select_related'].append(base_field_name)
                    
                    # Check for nested relationships
                    if len(source_parts) > 1 and relation_info.related_model:
                        self._analyze_nested_relationship(
                            relation_info.related_model, source_parts[1:], analysis
                        )
                else:
                    # ManyToMany or reverse relationship - use prefetch_related
                    if base_field_name not in analysis['prefetch_related']:
                        analysis['prefetch_related'].append(base_field_name)
            else:
                # Field not in relations, but might be a custom field that maps to a model field
                # Check if the field name matches a model ManyToMany field
                try:
                    model_field = model._meta.get_field(base_field_name)
                    if isinstance(model_field, ManyToManyField):
                        if base_field_name not in analysis['prefetch_related']:
                            analysis['prefetch_related'].append(base_field_name)
                except (models.FieldDoesNotExist, AttributeError):
                    # Field doesn't exist on model, might be a property or method
                    pass
        
        # Check if it's a nested serializer
        elif isinstance(field, serializers.Serializer):
            analysis['nested_serializers'].append(field_name)
            
            # First, ensure the base relationship is optimized
            if base_field_name in field_info.relations:
                relation_info = field_info.relations[base_field_name]
                if not relation_info.to_many:
                    # ForeignKey or OneToOneField - use select_related
                    if base_field_name not in analysis['select_related']:
                        analysis['select_related'].append(base_field_name)
                else:
                    # ManyToMany or reverse relationship - use prefetch_related
                    if base_field_name not in analysis['prefetch_related']:
                        analysis['prefetch_related'].append(base_field_name)
            
            # Check if the nested serializer has a model for deeper analysis
            try:
                if hasattr(field, 'Meta') and hasattr(field.Meta, 'model'):
                    nested_model = field.Meta.model
                    # Recursively analyze nested serializer
                    nested_analyzer = QueryAnalyzer(field.__class__)
                    nested_analysis = nested_analyzer.analyze()
                    
                    # Merge nested analysis
                    if source_parts:
                        base_field = source_parts[0]
                        # Add nested select_related/prefetch_related
                        for nested_field in nested_analysis.get('select_related', []):
                            full_path = f"{base_field}__{nested_field}"
                            if full_path not in analysis['select_related']:
                                analysis['select_related'].append(full_path)
                        
                        for nested_field in nested_analysis.get('prefetch_related', []):
                            full_path = f"{base_field}__{nested_field}"
                            if full_path not in analysis['prefetch_related']:
                                analysis['prefetch_related'].append(full_path)
            except Exception:
                # If nested serializer analysis fails, we've already handled the base relationship above
                pass
    
    
    def _analyze_nested_relationship(self, related_model, path_parts, analysis):
        """Analyze nested relationships (e.g., 'author__profile')."""
        if not path_parts:
            return
        
        try:
            field = related_model._meta.get_field(path_parts[0])
            if isinstance(field, (ForeignKey, OneToOneField)):
                full_path = '__'.join(path_parts)
                if full_path not in analysis['select_related']:
                    analysis['select_related'].append(full_path)
            elif isinstance(field, ManyToManyField):
                full_path = '__'.join(path_parts)
                if full_path not in analysis['prefetch_related']:
                    analysis['prefetch_related'].append(full_path)
        except models.FieldDoesNotExist:
            pass


def detect_n_plus_one(serializer_class, queryset):
    """
    Detect potential N+1 query issues for a serializer and queryset.
    
    Args:
        serializer_class: The serializer class to analyze
        queryset: The queryset that will be serialized
        
    Returns:
        List of warning messages about potential N+1 queries
    """
    warnings_list = []
    
    if not hasattr(queryset, 'query'):
        # Not a queryset, can't analyze
        return warnings_list
    
    analyzer = QueryAnalyzer(serializer_class)
    analysis = analyzer.analyze()
    
    # Check if queryset has optimizations
    query = queryset.query
    select_related = getattr(query, 'select_related', {})
    prefetch_related = getattr(query, 'prefetch_related_lookups', set())
    
    # Check for missing select_related
    for field in analysis.get('select_related', []):
        # If select_related is True, all fields are selected
        if select_related is True:
            continue
        elif isinstance(select_related, dict):
            if field not in select_related and not any(
                field.startswith(sel) for sel in select_related.keys()
            ):
                warnings_list.append(
                    f"Potential N+1 query detected: Consider using "
                    f"select_related('{field}') for field '{field}'"
                )
        else:
            # No select_related, add warning
            warnings_list.append(
                f"Potential N+1 query detected: Consider using "
                f"select_related('{field}') for field '{field}'"
            )
    
    # Check for missing prefetch_related
    for field in analysis.get('prefetch_related', []):
        if field not in prefetch_related and not any(
            field.startswith(pref) for pref in prefetch_related
        ):
            warnings_list.append(
                f"Potential N+1 query detected: Consider using "
                f"prefetch_related('{field}') for field '{field}'"
            )
    
    return warnings_list

