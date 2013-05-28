# Django REST framework 2

What it is, and why you should care.

> Most people just make the mistake that it should be simple to design simple things.  In reality, the effort required to design something is inversely proportional to the simplicity of the result.
>
> &mdash; [Roy Fielding][cite]

---

**Announcement:** REST framework 2 released - Tue 30th Oct 2012 

---

REST framework 2 is an almost complete reworking of the original framework, which comprehensively addresses some of the original design issues.

Because the latest version should be considered a re-release, rather than an incremental improvement, we've skipped a version, and called this release Django REST framework 2.0.

This article is intended to give you a flavor of what REST framework 2 is, and why you might want to give it a try.

## User feedback

Before we get cracking, let's start with the hard sell, with a few bits of feedback from some early adopters…

"Django REST framework 2 is beautiful.  Some of the API design is worthy of @kennethreitz." - [Kit La Touche][quote1]

"Since it's pretty much just Django, controlling things like URLs has been a breeze...  I think [REST framework 2] has definitely got the right approach here; even simple things like being able to override a function called post to do custom work during rather than having to intimately know what happens during a post make a huge difference to your productivity." - [Ian Strachan][quote2]

"I switched to the 2.0 branch and I don't regret it - fully refactored my code in another &half; day and it's *much* more to my tastes" - [Bruno Desthuilliers][quote3]

Sounds good, right?  Let's get into some details...

## Serialization

REST framework 2 includes a totally re-worked serialization engine, that was initially intended as a replacement for Django's existing inflexible fixture serialization, and which meets the following design goals:

* A declarative serialization API, that mirrors Django's `Forms`/`ModelForms` API.
* Structural concerns are decoupled from encoding concerns.
* Able to support rendering and parsing to many formats, including both machine-readable representations and HTML forms.
* Validation that can be mapped to obvious and comprehensive error responses. 
* Serializers that support both nested, flat, and partially-nested representations.
* Relationships that can be expressed as primary keys, hyperlinks, slug fields, and other custom representations.

Mapping between the internal state of the system and external representations of that state is the core concern of building Web APIs.  Designing serializers that allow the developer to do so in a flexible and obvious way is a deceptively difficult design task, and with the new serialization API we think we've pretty much nailed it.

## Generic views

When REST framework was initially released at the start of 2011, the current Django release was version 1.2.  REST framework included a backport of Django 1.3's upcoming `View` class, but it didn't take full advantage of the generic view implementations.

With the new release the generic views in REST framework now tie in with Django's generic views.  The end result is that framework is clean, lightweight and easy to use.

## Requests, Responses & Views

REST framework 2 includes `Request` and `Response` classes, than are used in place of Django's existing `HttpRequest` and `HttpResponse` classes.  Doing so allows logic such as parsing the incoming request or rendering the outgoing response to be supported transparently by the framework.

The `Request`/`Response` approach leads to a much cleaner API, less logic in the view itself, and a simple, obvious request-response cycle.

REST framework 2 also allows you to work with both function-based and class-based views.  For simple API views all you need is a single `@api_view` decorator, and you're good to go.


## API Design

Pretty much every aspect of REST framework has been reworked, with the aim of ironing out some of the design flaws of the previous versions.  Each of the components of REST framework are cleanly decoupled, and can be used independently of each-other, and there are no monolithic resource classes, overcomplicated mixin combinations, or opinionated serialization or URL routing decisions.

## The Browsable API

Django REST framework's most unique feature is the way it is able to serve up both machine-readable representations, and a fully browsable HTML representation to the same endpoints.

Browsable Web APIs are easier to work with, visualize and debug, and generally makes it easier and more frictionless to inspect and work with.

With REST framework 2, the browsable API gets a snazzy new bootstrap-based theme that looks great and is even nicer to work with.

There are also some functionality improvements - actions such as as `POST` and `DELETE` will only display if the user has the appropriate permissions.

![Browsable API][image]

**Image above**: An example of the browsable API in REST framework 2

## Documentation

As you can see the documentation for REST framework has been radically improved.  It gets a completely new style, using markdown for the documentation source, and a bootstrap-based theme for the styling.

We're really pleased with how the docs style looks - it's simple and clean, is easy to navigate around, and we think it reads great.

## Summary

In short, we've engineered the hell outta this thing, and we're incredibly proud of the result.

If you're interested please take a browse around the documentation.  [The tutorial][tut] is a great place to get started.

There's also a [live sandbox version of the tutorial API][sandbox] available for testing.

[cite]: http://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven#comment-724
[quote1]: https://twitter.com/kobutsu/status/261689665952833536
[quote2]: https://groups.google.com/d/msg/django-rest-framework/heRGHzG6BWQ/ooVURgpwVC0J
[quote3]: https://groups.google.com/d/msg/django-rest-framework/flsXbvYqRoY/9lSyntOf5cUJ
[image]: ../img/quickstart.png
[readthedocs]: https://readthedocs.org/
[tut]: ../tutorial/1-serialization.md
[sandbox]: http://restframework.herokuapp.com/
