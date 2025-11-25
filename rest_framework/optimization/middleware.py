"""
Middleware for detecting N+1 queries in development mode.

This middleware can be added to Django's MIDDLEWARE setting to automatically
detect and warn about N+1 query problems during development.
"""

import warnings
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin


class QueryOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware that detects potential N+1 queries in development mode.
    
    This middleware tracks database queries and warns when patterns that
    suggest N+1 queries are detected.
    
    Usage:
        Add to MIDDLEWARE in settings.py:
        
        MIDDLEWARE = [
            ...
            'rest_framework.optimization.middleware.QueryOptimizationMiddleware',
        ]
    
    Settings:
        - QUERY_OPTIMIZATION_WARN_THRESHOLD: Number of similar queries to trigger warning (default: 5)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.warn_threshold = getattr(
            settings,
            'QUERY_OPTIMIZATION_WARN_THRESHOLD',
            5
        )
        super().__init__(get_response)
    
    def process_request(self, request):
        """Reset query tracking for each request."""
        if settings.DEBUG:
            connection.queries_log.clear()
        return None
    
    def process_response(self, request, response):
        """Analyze queries and warn about potential N+1 issues."""
        if not settings.DEBUG:
            return response
        
        try:
            # In Django 5.2+, use queries_log, fallback to queries for older versions
            if hasattr(connection, 'queries_log'):
                queries = connection.queries_log
            else:
                queries = getattr(connection, 'queries', [])
            
            if len(queries) > self.warn_threshold:
                # Analyze queries for patterns
                self._analyze_queries(queries, request)
        except Exception as e:
            # Don't break the request if analysis fails
            import traceback
            if settings.DEBUG:
                # Only log in DEBUG mode to avoid noise
                warnings.warn(f"Query optimization middleware error: {e}", UserWarning)
        
        return response
    
    def _analyze_queries(self, queries, request):
        """Analyze queries for N+1 patterns."""
        # Group queries by SQL pattern
        query_patterns = {}
        for query in queries:
            # Handle both dict format (old Django) and string format (new Django)
            if isinstance(query, dict):
                sql = query.get('sql', '')
            elif isinstance(query, str):
                sql = query
            else:
                # Django 5.2+ might use a different format
                sql = str(query)
            
            if not sql:
                continue
                
            # Normalize SQL (remove values, keep structure)
            normalized = self._normalize_sql(sql)
            if normalized not in query_patterns:
                query_patterns[normalized] = []
            query_patterns[normalized].append(query)
        
        # Warn about patterns that appear many times (potential N+1)
        for pattern, query_list in query_patterns.items():
            if len(query_list) >= self.warn_threshold:
                # Check if it's a SELECT query (not INSERT/UPDATE/DELETE)
                if 'SELECT' in pattern.upper():
                    warnings.warn(
                        f"Potential N+1 query detected: {len(query_list)} similar queries "
                        f"executed for pattern: {pattern[:100]}... "
                        f"Consider using select_related() or prefetch_related().",
                        UserWarning
                    )
    
    def _normalize_sql(self, sql):
        """Normalize SQL by removing values and keeping structure."""
        import re
        # Remove quoted strings
        sql = re.sub(r"'[^']*'", "'?'", sql)
        sql = re.sub(r'"[^"]*"', '"?"', sql)
        # Remove numbers
        sql = re.sub(r'\b\d+\b', '?', sql)
        # Normalize whitespace
        sql = ' '.join(sql.split())
        return sql

