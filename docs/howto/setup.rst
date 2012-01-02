.. _setup:

Setup
=====

Installing into site-packages
-----------------------------

If you need to manually install Django REST framework to your ``site-packages`` directory, run the ``setup.py`` script::

    python setup.py install

Template Loaders
----------------

Django REST framework uses a few templates for the HTML and plain text documenting renderers.

* Ensure ``TEMPLATE_LOADERS`` setting contains ``'django.template.loaders.app_directories.Loader'``.

This will be the case by default so you shouldn't normally need to do anything here.

Admin Styling
-------------

Django REST framework uses the admin media for styling.  When running using Django's testserver this is automatically served for you, 
but once you move onto a production server, you'll want to make sure you serve the admin media separately, exactly as you would do 
`if using the Django admin <https://docs.djangoproject.com/en/dev/howto/deployment/modpython/#serving-the-admin-files>`_.

* Ensure that the ``ADMIN_MEDIA_PREFIX`` is set appropriately and that you are serving the admin media. 
  (Django's testserver will automatically serve the admin media for you)

Markdown
--------

The Python `markdown library <http://www.freewisdom.org/projects/python-markdown/>`_ is not required but comes recommended.

If markdown is installed your :class:`.Resource` descriptions can include `markdown style formatting 
<http://daringfireball.net/projects/markdown/syntax>`_ which will be rendered by the HTML documenting renderer.

robots.txt, favicon, login/logout
---------------------------------

Django REST framework comes with a few views that can be useful including a deny robots view, a favicon view, and api login and logout views::

    from django.conf.urls.defaults import patterns

    urlpatterns = patterns('djangorestframework.views',
        (r'robots.txt', 'deny_robots'),
        (r'favicon.ico', 'favicon'),
        # Add your resources here
        (r'^accounts/login/$', 'api_login'),
        (r'^accounts/logout/$', 'api_logout'),
    )

