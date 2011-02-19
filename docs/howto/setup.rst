.. _setup:

Setup
=====

Template Loaders
----------------

Django REST framework uses a few templates for the HTML and plain text documenting emitters.

* Ensure ``TEMPLATE_LOADERS`` setting contains ``'django.template.loaders.app_directories.Loader'``.

This will be the case by default so you shouldn't normally need to do anything here.

Admin Styling
-------------

Django REST framework uses the admin media for styling.  When running using Django's testserver this is automatically served for you, but once you move onto a production server, you'll want to make sure you serve the admin media seperatly, exactly as you would do if using the Django admin.

* Ensure that the ``ADMIN_MEDIA_PREFIX`` is set appropriately and that you are serving the admin media.  (Django's testserver will automatically serve the admin media for you)

Markdown
--------

The Python `markdown library <http://www.freewisdom.org/projects/python-markdown/>`_ is not required but comes recommended.

If markdown is installed your :class:`.Resource` descriptions can include `markdown style formatting <http://daringfireball.net/projects/markdown/syntax>`_ which will be rendered by the HTML documenting emitter.

