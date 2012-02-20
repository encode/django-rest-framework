.. _setup:

Setup
=====

Templates
---------

Django REST framework uses a few templates for the HTML and plain text
documenting renderers.  You'll need to ensure ``TEMPLATE_LOADERS`` setting
contains ``'django.template.loaders.app_directories.Loader'``.
This will already be the case by default.

You may customize the templates by creating a new template called
``djangorestframework/api.html`` in your project, which should extend
``djangorestframework/base.html`` and override the appropriate
block tags. For example::

    {% extends "djangorestframework/base.html" %}

    {% block title %}My API{% endblock %}

    {% block branding %}
    <h1 id="site-name">My API</h1>
    {% endblock %}


Styling
-------

Django REST framework requires `django.contrib.staticfiles`_ to serve it's css.
If you're using Django 1.2 you'll need to use the seperate
`django-staticfiles`_ package instead.

You can override the styling by creating a file in your top-level static
directory named ``djangorestframework/css/style.css``


Markdown
--------

`Python markdown`_ is not required but comes recommended.

If markdown is installed your :class:`.Resource` descriptions can include
`markdown formatting`_ which will be rendered by the self-documenting API.

YAML
----

YAML support is optional, and requires `PyYAML`_.


Login / Logout
--------------

Django REST framework includes login and logout views that are useful if
you're using the self-documenting API::

    from django.conf.urls.defaults import patterns

    urlpatterns = patterns('djangorestframework.views',
        # Add your resources here
        (r'^accounts/login/$', 'api_login'),
        (r'^accounts/logout/$', 'api_logout'),
    )

.. _django.contrib.staticfiles: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/
.. _django-staticfiles: http://pypi.python.org/pypi/django-staticfiles/
.. _URLObject: http://pypi.python.org/pypi/URLObject/
.. _Python markdown: http://www.freewisdom.org/projects/python-markdown/
.. _markdown formatting: http://daringfireball.net/projects/markdown/syntax
.. _PyYAML: http://pypi.python.org/pypi/PyYAML