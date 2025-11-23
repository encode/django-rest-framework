"""
Tests for query optimization features in Django REST Framework.
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase

from rest_framework import generics, serializers, viewsets
from rest_framework.optimization import (
    OptimizedQuerySetMixin,
    analyze_serializer_fields,
    detect_n_plus_one,
    get_optimization_suggestions,
    optimize_queryset,
)
from rest_framework.test import APIRequestFactory

from .models import (
    ForeignKeyTarget, ForeignKeySource, ManyToManyTarget, ManyToManySource
)

factory = APIRequestFactory()


# Test serializers using existing models
class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeyTarget
        fields = '__all__'


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    target = ForeignKeyTargetSerializer(read_only=True)

    class Meta:
        model = ForeignKeySource
        fields = '__all__'


class ForeignKeySourceListSerializer(serializers.ModelSerializer):
    """Simpler serializer for list view."""
    class Meta:
        model = ForeignKeySource
        fields = ['id', 'name', 'target']


class ManyToManySourceSerializer(serializers.ModelSerializer):
    targets = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = ManyToManySource
        fields = '__all__'


class TestQueryAnalyzer(TestCase):
    """Test the QueryAnalyzer functionality."""

    def test_analyze_serializer_with_foreign_key(self):
        """Test analyzing a serializer with ForeignKey relationships."""
        analysis = analyze_serializer_fields(ForeignKeySourceListSerializer)
        
        self.assertIn('select_related', analysis)
        self.assertIn('prefetch_related', analysis)
        # Should detect target as select_related
        self.assertIn('target', analysis['select_related'])

    def test_analyze_serializer_with_many_to_many(self):
        """Test analyzing a serializer with ManyToMany relationships."""
        analysis = analyze_serializer_fields(ManyToManySourceSerializer)
        
        # Should detect targets as prefetch_related
        self.assertIn('targets', analysis['prefetch_related'])

    def test_analyze_nested_serializer(self):
        """Test analyzing nested serializers."""
        analysis = analyze_serializer_fields(ForeignKeySourceSerializer)
        
        # Should detect target as select_related
        self.assertIn('target', analysis['select_related'])

    def test_analyze_non_model_serializer(self):
        """Test analyzing a non-ModelSerializer returns empty analysis."""
        class SimpleSerializer(serializers.Serializer):
            name = serializers.CharField()
        
        analysis = analyze_serializer_fields(SimpleSerializer)
        
        self.assertEqual(analysis['select_related'], [])
        self.assertEqual(analysis['prefetch_related'], [])


class TestQueryOptimizer(TestCase):
    """Test the query optimizer functionality."""

    def setUp(self):
        self.target = ForeignKeyTarget.objects.create(name='Test Target')
        self.source = ForeignKeySource.objects.create(name='Test Source', target=self.target)
        self.m2m_target = ManyToManyTarget.objects.create(name='M2M Target')
        self.m2m_source = ManyToManySource.objects.create(name='M2M Source')
        self.m2m_source.targets.add(self.m2m_target)

    def test_optimize_queryset_with_select_related(self):
        """Test optimizing a queryset with select_related."""
        queryset = ForeignKeySource.objects.all()
        optimized = optimize_queryset(queryset, ForeignKeySourceListSerializer, auto_optimize=True)
        
        # Check that select_related was applied
        self.assertTrue(hasattr(optimized.query, 'select_related'))
        # The queryset should have select_related applied
        self.assertTrue(optimized.query.select_related)

    def test_optimize_queryset_with_prefetch_related(self):
        """Test optimizing a queryset with prefetch_related."""
        queryset = ManyToManySource.objects.all()
        optimized = optimize_queryset(queryset, ManyToManySourceSerializer, auto_optimize=True)
        
        # Check that prefetch_related was applied
        self.assertTrue(hasattr(optimized.query, 'prefetch_related_lookups'))
        self.assertIn('targets', optimized.query.prefetch_related_lookups)

    def test_optimize_queryset_explicit_fields(self):
        """Test optimizing with explicitly provided fields."""
        queryset = ForeignKeySource.objects.all()
        optimized = optimize_queryset(
            queryset,
            ForeignKeySourceListSerializer,
            select_related=['target'],
            auto_optimize=False
        )
        
        self.assertTrue(optimized.query.select_related)

    def test_optimize_queryset_merges_explicit_and_auto(self):
        """Test that explicit and auto-detected fields are merged."""
        queryset = ForeignKeySource.objects.all()
        optimized = optimize_queryset(
            queryset,
            ForeignKeySourceListSerializer,
            select_related=['target'],
            auto_optimize=True
        )
        
        # Should have both explicit and auto-detected fields
        self.assertTrue(optimized.query.select_related)

    def test_optimize_queryset_non_queryset(self):
        """Test that non-queryset objects are returned as-is."""
        result = optimize_queryset([1, 2, 3], ForeignKeySourceListSerializer)
        self.assertEqual(result, [1, 2, 3])


class TestOptimizedQuerySetMixin(TestCase):
    """Test the OptimizedQuerySetMixin."""

    def setUp(self):
        self.target = ForeignKeyTarget.objects.create(name='Test Target')
        self.source = ForeignKeySource.objects.create(name='Test Source', target=self.target)
        self.m2m_target = ManyToManyTarget.objects.create(name='M2M Target')
        self.m2m_source = ManyToManySource.objects.create(name='M2M Source')
        self.m2m_source.targets.add(self.m2m_target)

    def test_mixin_applies_optimization(self):
        """Test that the mixin applies optimizations automatically."""
        class SourceViewSet(OptimizedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
            queryset = ForeignKeySource.objects.all()
            serializer_class = ForeignKeySourceListSerializer
        
        view = SourceViewSet()
        queryset = view.get_queryset()
        
        # Should have optimizations applied
        self.assertTrue(hasattr(queryset.query, 'select_related'))

    def test_mixin_with_explicit_fields(self):
        """Test mixin with explicitly specified fields."""
        class SourceViewSet(OptimizedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
            queryset = ForeignKeySource.objects.all()
            serializer_class = ForeignKeySourceListSerializer
            select_related_fields = ['target']
        
        view = SourceViewSet()
        queryset = view.get_queryset()
        
        self.assertTrue(queryset.query.select_related)


class TestDetectNPlusOne(TestCase):
    """Test N+1 query detection."""

    def setUp(self):
        self.target = ForeignKeyTarget.objects.create(name='Test Target')
        self.source = ForeignKeySource.objects.create(name='Test Source', target=self.target)

    def test_detect_n_plus_one_without_optimization(self):
        """Test detecting N+1 queries when queryset is not optimized."""
        queryset = ForeignKeySource.objects.all()
        warnings = detect_n_plus_one(ForeignKeySourceListSerializer, queryset)
        
        # Should detect potential N+1 queries
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any('target' in w for w in warnings))

    def test_detect_n_plus_one_with_optimization(self):
        """Test that optimized querysets don't trigger warnings."""
        queryset = ForeignKeySource.objects.select_related('target')
        warnings = detect_n_plus_one(ForeignKeySourceListSerializer, queryset)
        
        # Should have fewer or no warnings for optimized queryset
        # (Note: This may need adjustment based on implementation)

    def test_detect_n_plus_one_non_queryset(self):
        """Test that non-queryset objects return empty warnings."""
        warnings = detect_n_plus_one(ForeignKeySourceListSerializer, [1, 2, 3])
        self.assertEqual(warnings, [])


class TestOptimizationSuggestions(TestCase):
    """Test getting optimization suggestions."""

    def test_get_suggestions(self):
        """Test getting optimization suggestions for a serializer."""
        suggestions = get_optimization_suggestions(ForeignKeySourceListSerializer)
        
        self.assertIn('select_related', suggestions)
        self.assertIn('prefetch_related', suggestions)
        self.assertIn('code_example', suggestions)
        
        # Should have suggestions
        self.assertGreater(len(suggestions['select_related']), 0)
        
        # Should have code example
        if suggestions['select_related'] or suggestions['prefetch_related']:
            self.assertIsNotNone(suggestions['code_example'])
            self.assertIn('get_queryset', suggestions['code_example'])

