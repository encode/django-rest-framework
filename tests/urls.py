"""
URLConf for test suite.

We need only the docs urls for DocumentationRenderer tests.
"""
from django.urls import path

from rest_framework.compat import coreapi
from rest_framework.documentation import include_docs_urls

if coreapi:
    urlpatterns = [
        path('docs/', include_docs_urls(title='Test Suite API')),
    ]
else:
    urlpatterns = []
