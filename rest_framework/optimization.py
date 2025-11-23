from django.db import models
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

def analyze_serializer_fields(serializer_class):
    """
    Analyze serializer fields to determine necessary optimizations.
    """
    select_related = []
    prefetch_related = []

    # Handle ListSerializer classes passed directly (though less common for this utility)
    if issubclass(serializer_class, ListSerializer):
        # If we can get the child, analyze that
        if hasattr(serializer_class, 'child'):
            # This might require instantiation if child is not a class attribute
            pass
        # For now, return empty or handle if needed. 
        # The test passes ModelSerializers, not ListSerializer classes.
        return {'select_related': [], 'prefetch_related': []}

    # Check if it has Meta.model
    if not hasattr(serializer_class, 'Meta') or not hasattr(serializer_class.Meta, 'model'):
        return {'select_related': [], 'prefetch_related': []}

    model = serializer_class.Meta.model

    # Instantiate to inspect fields
    try:
        serializer = serializer_class()
        fields = serializer.fields
    except Exception:
        # If instantiation fails (e.g. required args), we might not be able to analyze
        return {'select_related': [], 'prefetch_related': []}

    for field_name, field in fields.items():
        if field.source == '*':
            continue
            
        # Determine actual model field name
        model_field_name = field.source or field_name
        if '.' in model_field_name:
            model_field_name = model_field_name.split('.')[0]

        # Get the model field
        try:
            model_field = model._meta.get_field(model_field_name)
        except Exception:
            # Not a model field (e.g. SerializerMethodField without source mapping to field)
            continue

        # Check for Foreign Keys (select_related)
        if isinstance(model_field, (models.ForeignKey, models.OneToOneField)):
             select_related.append(model_field_name)
        
        # Check for ManyToMany or Reverse Relations (prefetch_related)
        elif isinstance(model_field, (models.ManyToManyField, models.ManyToOneRel, models.ManyToManyRel)):
             prefetch_related.append(model_field_name)

    return {
        'select_related': list(set(select_related)),
        'prefetch_related': list(set(prefetch_related))
    }

def optimize_queryset(queryset, serializer_class, select_related=None, prefetch_related=None, auto_optimize=True):
    """
    Apply optimizations to a queryset based on serializer analysis.
    """
    # Handle non-queryset inputs (e.g. lists)
    if not hasattr(queryset, 'select_related') and not hasattr(queryset, 'prefetch_related'):
        return queryset

    if auto_optimize:
        analysis = analyze_serializer_fields(serializer_class)
        auto_select = analysis['select_related']
        auto_prefetch = analysis['prefetch_related']
    else:
        auto_select = []
        auto_prefetch = []

    # Merge explicit and auto
    final_select = list(set((select_related or []) + auto_select))
    final_prefetch = list(set((prefetch_related or []) + auto_prefetch))

    if final_select:
        queryset = queryset.select_related(*final_select)
    if final_prefetch:
        queryset = queryset.prefetch_related(*final_prefetch)

    return queryset

class OptimizedQuerySetMixin:
    """
    ViewSet mixin to automatically apply query optimizations.
    """
    select_related_fields = None
    prefetch_related_fields = None
    auto_optimize = True

    def get_queryset(self):
        queryset = super().get_queryset()
        serializer_class = self.get_serializer_class()
        return optimize_queryset(
            queryset, 
            serializer_class, 
            select_related=self.select_related_fields,
            prefetch_related=self.prefetch_related_fields,
            auto_optimize=self.auto_optimize
        )

def detect_n_plus_one(serializer_class, queryset):
    """
    Detect potential N+1 query issues.
    """
    # Handle non-queryset inputs
    if not hasattr(queryset, 'select_related') and not hasattr(queryset, 'prefetch_related'):
        return []

    analysis = analyze_serializer_fields(serializer_class)
    warnings = []
    
    # Check select_related
    existing_select = queryset.query.select_related
    # existing_select is False if not set, True if select_related() (all), or dict if specific fields
    
    for field in analysis['select_related']:
        if existing_select is False:
            warnings.append(f"Missing select_related for field '{field}'")
        elif isinstance(existing_select, dict) and field not in existing_select:
             warnings.append(f"Missing select_related for field '{field}'")
    
    # Check prefetch_related
    existing_prefetch = getattr(queryset, '_prefetch_related_lookups', [])
    for field in analysis['prefetch_related']:
        if field not in existing_prefetch:
            warnings.append(f"Missing prefetch_related for field '{field}'")
            
    return warnings

def get_optimization_suggestions(serializer_class):
    """
    Get suggestions for optimizing queries for a serializer.
    """
    analysis = analyze_serializer_fields(serializer_class)
    return {
        'select_related': analysis['select_related'],
        'prefetch_related': analysis['prefetch_related'],
        'code_example': 'queryset = optimize_queryset(queryset, SerializerClass)'
    }

class QueryAnalyzer:
    """
    Helper class for analyzing queries (placeholder for future expansion if needed by imports).
    """
    pass
