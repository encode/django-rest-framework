# REST, Hypermedia & HATEOAS

> You keep using that word "REST". I do not think it means what you think it means.
>
> &mdash; Mike Amundsen, [REST fest 2012 keynote][cite].

First off, the disclaimer.  The name "Django REST framework" was choosen with a view to making sure the project would be easily found by developers.  Throughout the documentation we try to use the more simple and technically correct terminology of "Web APIs".

If you are serious about designing a Hypermedia APIs, you should look to resources outside of this documentation to help inform your design choices.

The following fall into the "required reading" category.

* Fielding's dissertation - [Architectural Styles and
the Design of Network-based Software Architectures][dissertation].
* Fielding's "[REST APIs must be hypertext-driven][hypertext-driven]" blog post.
* Leonard Richardson & Sam Ruby's [RESTful Web Services][restful-web-services].
* Mike Amundsen's [Building Hypermedia APIs with HTML5 and Node][building-hypermedia-apis].
* Steve Klabnik's [Designing Hypermedia APIs][designing-hypermedia-apis].
* The [Richardson Maturity Model][maturitymodel].

For a more thorough background, check out Klabnik's [Hypermedia API reading list][readinglist].

# Building Hypermedia APIs with REST framework

REST framework is an agnositic Web API toolkit.  It does help guide you towards building well-connected APIs, and makes it easy to design appropriate media types, but it does not strictly enforce any particular design style.

### What REST framework *does* provide.

It is self evident that REST framework makes it possible to build Hypermedia APIs.  The browseable API that it offers is built on HTML - the hypermedia language of the web.

REST framework also includes [serialization] and [parser]/[renderer] components that make it easy to build appropriate media types, [hyperlinked relations][fields] for building well-connected systems, and great support for [content negotiation][conneg].

### What REST framework *doesn't* provide.

What REST framework doesn't do is give you is machine readable hypermedia formats such as [Collection+JSON][collection] by default, or the ability to auto-magically create HATEOAS style APIs.  Doing so would involve making opinionated choices about API design that should really remain outside of the framework's scope.

[cite]: http://vimeo.com/channels/restfest/page:2
[dissertation]: http://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm
[hypertext-driven]: http://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven
[restful-web-services]: 
[building-hypermedia-apis]: …
[designing-hypermedia-apis]: http://designinghypermediaapis.com/
[restisover]: http://blog.steveklabnik.com/posts/2012-02-23-rest-is-over
[readinglist]: http://blog.steveklabnik.com/posts/2012-02-27-hypermedia-api-reading-list
[maturitymodel]: http://martinfowler.com/articles/richardsonMaturityModel.html

[collection]: http://www.amundsen.com/media-types/collection/
[serialization]: ../api-guide/serializers.md
[parser]: ../api-guide/parsers.md
[renderer]: ../api-guide/renderers.md
[fields]: ../api-guide/fields.md
[conneg]: ../api-guide/content-negotiation.md