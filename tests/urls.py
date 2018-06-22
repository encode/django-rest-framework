"""
URLConf for test suite.

We need only the docs urls for DocumentationRenderer tests.
"""
from django.conf.urls import url

from rest_framework.compat import coreapi
from rest_framework.documentation import include_docs_urls

if coreapi:
    urlpatterns = [
        url(r'^docs/', include_docs_urls(title='Test Suite API')),
    ]
else:
    urlpatterns = []
