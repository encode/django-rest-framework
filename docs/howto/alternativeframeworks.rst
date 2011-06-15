Alternative frameworks & Why Django REST framework
==================================================

Alternative frameworks
----------------------

There are a number of alternative REST frameworks for Django:

* `django-piston <https://bitbucket.org/jespern/django-piston/wiki/Home>`_ is very mature, and has a large community behind it.  This project was originally based on piston code in parts.
* `django-tasypie <https://github.com/toastdriven/django-tastypie>`_ is also very good, and has a very active and helpful developer community and maintainers.
* Other interesting projects include `dagny <https://github.com/zacharyvoase/dagny>`_ and `dj-webmachine <http://benoitc.github.com/dj-webmachine/>`_


Why use Django REST framework?
------------------------------

The big benefits of using Django REST framework come down to:

1. It's based on Django's class based views, which makes it simple, modular, and future-proof.
2. It stays as close as possible to Django idioms and language throughout.
3. The browse-able API makes working with the APIs extremely quick and easy.


Why was this project created?
-----------------------------

For me the browse-able API is the most important aspect of Django REST framework.

I wanted to show that Web APIs could easily be made Web browse-able,
and demonstrate how much better browse-able Web APIs are to work with.

Being able to navigate and use a Web API directly in the browser is a huge win over only having command line and programmatic
access to the API.  It enables the API to be properly self-describing, and it makes it much much quicker and easier to work with.
There's no fundamental reason why the Web APIs we're creating shouldn't be able to render to HTML as well as JSON/XML/whatever,
and I really think that more Web API frameworks *in whatever language* ought to be taking a similar approach.
