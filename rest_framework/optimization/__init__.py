"""
Query optimization utilities for Django REST Framework.

This module provides tools to automatically detect and prevent N+1 query problems
in DRF serializers by analyzing serializer fields and optimizing querysets.
"""

from rest_framework.optimization.mixins import OptimizedQuerySetMixin
from rest_framework.optimization.optimizer import (
    optimize_queryset,
    analyze_serializer_fields,
    get_optimization_suggestions,
)
from rest_framework.optimization.query_analyzer import (
    QueryAnalyzer,
    detect_n_plus_one,
)

__all__ = [
    'OptimizedQuerySetMixin',
    'optimize_queryset',
    'analyze_serializer_fields',
    'get_optimization_suggestions',
    'QueryAnalyzer',
    'detect_n_plus_one',
]

