"""
Query optimizer for automatically optimizing querysets based on serializer fields.

This module provides utilities to automatically apply select_related and
prefetch_related optimizations to querysets based on serializer field analysis.
"""

from django.db.models import QuerySet

from rest_framework import serializers

from rest_framework.optimization.query_analyzer import QueryAnalyzer


def analyze_serializer_fields(serializer_class):
    """
    Analyze a serializer class to identify required query optimizations.
    
    Args:
        serializer_class: The serializer class to analyze
        
    Returns:
        Dictionary with 'select_related' and 'prefetch_related' lists
    """
    analyzer = QueryAnalyzer(serializer_class)
    return analyzer.analyze()


def optimize_queryset(
    queryset,
    serializer_class,
    select_related=None,
    prefetch_related=None,
    auto_optimize=True
):
    """
    Optimize a queryset based on serializer analysis and/or explicit parameters.
    
    Args:
        queryset: The queryset to optimize
        serializer_class: The serializer class that will be used
        select_related: Explicit list of fields for select_related (optional)
        prefetch_related: Explicit list of fields for prefetch_related (optional)
        auto_optimize: If True, automatically analyze serializer and apply optimizations
        
    Returns:
        Optimized queryset
    """
    if not isinstance(queryset, QuerySet):
        return queryset
    
    # Start with the original queryset
    optimized = queryset
    
    # Auto-optimize based on serializer analysis
    if auto_optimize:
        analysis = analyze_serializer_fields(serializer_class)
        
        # Merge auto-detected with explicit parameters
        if select_related is None:
            select_related = analysis.get('select_related', [])
        else:
            # Merge lists, avoiding duplicates
            auto_select = analysis.get('select_related', [])
            select_related = list(set(select_related + auto_select))
        
        if prefetch_related is None:
            prefetch_related = analysis.get('prefetch_related', [])
        else:
            # Merge lists, avoiding duplicates
            auto_prefetch = analysis.get('prefetch_related', [])
            prefetch_related = list(set(prefetch_related + auto_prefetch))
    
    # Apply select_related
    if select_related:
        # Check if queryset already has select_related
        existing_select = getattr(optimized.query, 'select_related', {})
        
        # Handle case where select_related is True (all fields selected)
        if existing_select is True:
            # All fields already selected, skip
            new_select = []
        elif isinstance(existing_select, dict):
            # Only add fields that aren't already selected
            new_select = [
                field for field in select_related
                if field not in existing_select and not any(
                    field.startswith(sel) for sel in existing_select.keys()
                )
            ]
        else:
            # Empty or unknown format, add all
            new_select = select_related
        
        if new_select:
            if len(new_select) == 1:
                optimized = optimized.select_related(new_select[0])
            else:
                optimized = optimized.select_related(*new_select)
    
    # Apply prefetch_related
    if prefetch_related:
        # Check if queryset already has prefetch_related
        existing_prefetch = getattr(optimized.query, 'prefetch_related_lookups', set())
        
        # Only add fields that aren't already prefetched
        new_prefetch = [
            field for field in prefetch_related
            if field not in existing_prefetch and not any(
                field.startswith(pref) for pref in existing_prefetch
            )
        ]
        
        if new_prefetch:
            for field in new_prefetch:
                optimized = optimized.prefetch_related(field)
    
    return optimized


def get_optimization_suggestions(serializer_class):
    """
    Get optimization suggestions for a serializer class.
    
    Args:
        serializer_class: The serializer class to analyze
        
    Returns:
        Dictionary with optimization suggestions and code examples
    """
    analysis = analyze_serializer_fields(serializer_class)
    
    suggestions = {
        'select_related': analysis.get('select_related', []),
        'prefetch_related': analysis.get('prefetch_related', []),
        'nested_serializers': analysis.get('nested_serializers', []),
        'code_example': None
    }
    
    # Generate code example
    if suggestions['select_related'] or suggestions['prefetch_related']:
        parts = []
        
        if suggestions['select_related']:
            if len(suggestions['select_related']) == 1:
                parts.append(f".select_related('{suggestions['select_related'][0]}')")
            else:
                fields_str = "', '".join(suggestions['select_related'])
                parts.append(f".select_related('{fields_str}')")
        
        if suggestions['prefetch_related']:
            for field in suggestions['prefetch_related']:
                parts.append(f".prefetch_related('{field}')")
        
        if parts:
            suggestions['code_example'] = (
                "def get_queryset(self):\n"
                "    queryset = super().get_queryset()\n"
                f"    return queryset{''.join(parts)}"
            )
    
    return suggestions

