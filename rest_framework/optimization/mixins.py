"""
Mixins for automatic query optimization in Django REST Framework viewsets.

This module provides mixins that automatically optimize querysets based on
serializer field analysis.
"""

import warnings

from django.db.models import QuerySet

from rest_framework.settings import api_settings

from rest_framework.optimization.optimizer import optimize_queryset
from rest_framework.optimization.query_analyzer import detect_n_plus_one


class OptimizedQuerySetMixin:
    """
    Mixin that automatically optimizes querysets based on serializer analysis.
    
    This mixin can be added to any GenericAPIView or ViewSet to automatically
    apply select_related and prefetch_related optimizations based on the
    serializer's field definitions.
    
    Usage:
        class MyViewSet(OptimizedQuerySetMixin, ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
    
    You can also explicitly specify optimizations:
        class MyViewSet(OptimizedQuerySetMixin, ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
            select_related_fields = ['author', 'category']
            prefetch_related_fields = ['tags', 'comments']
    
    Settings:
        - ENABLE_QUERY_OPTIMIZATION: Enable/disable automatic optimization (default: True)
        - WARN_ON_N_PLUS_ONE: Show warnings when N+1 queries are detected (default: True in DEBUG)
    """
    
    # Explicit optimization fields (optional)
    select_related_fields = None
    prefetch_related_fields = None
    
    # Control optimization behavior
    enable_auto_optimization = True
    warn_on_n_plus_one = None
    
    def get_queryset(self):
        """
        Get the queryset with automatic optimizations applied.
        
        This method extends the base get_queryset() to automatically apply
        select_related and prefetch_related based on serializer analysis.
        """
        queryset = super().get_queryset()
        
        # Check if optimization is enabled
        enable_optimization = getattr(
            api_settings,
            'ENABLE_QUERY_OPTIMIZATION',
            self.enable_auto_optimization
        )
        
        if not enable_optimization:
            return queryset
        
        # Get serializer class
        serializer_class = self.get_serializer_class()
        if not serializer_class:
            return queryset
        
        # Optimize queryset
        try:
            queryset = optimize_queryset(
                queryset,
                serializer_class,
                select_related=self.select_related_fields,
                prefetch_related=self.prefetch_related_fields,
                auto_optimize=self.enable_auto_optimization
            )
        except Exception as e:
            # If optimization fails, log warning but don't break
            if self._should_warn():
                warnings.warn(
                    f"Query optimization failed: {e}. "
                    f"Continuing with unoptimized queryset.",
                    UserWarning
                )
            return queryset
        
        # Check for N+1 queries and warn if enabled
        if self._should_warn():
            warnings_list = detect_n_plus_one(serializer_class, queryset)
            for warning_msg in warnings_list:
                warnings.warn(warning_msg, UserWarning)
        
        return queryset
    
    def _should_warn(self):
        """Determine if warnings should be shown."""
        if self.warn_on_n_plus_one is not None:
            return self.warn_on_n_plus_one
        
        # Default: warn in DEBUG mode
        from django.conf import settings
        warn_on_n_plus_one = getattr(
            api_settings,
            'WARN_ON_N_PLUS_ONE',
            getattr(settings, 'DEBUG', False)
        )
        return warn_on_n_plus_one


# Backward compatibility alias
QueryOptimizationMixin = OptimizedQuerySetMixin

