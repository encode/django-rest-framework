# Contributing to REST framework

> The world can only really be changed one piece at a time.  The art is picking that piece.
>
> &mdash; [Tim Berners-Lee][cite]

There are many ways you can contribute to Django REST framework.  We'd like it to be a community-led project, so please get involved and help shape the future of the project.

# Community

If you use and enjoy REST framework please consider [staring the project on GitHub][github], and [upvoting it on Django packages][django-packages].  Doing so helps potential new users see that the project is well used, and help us continue to attract new users.

You might also consider writing a blog post on your experience with using REST framework, writing a tutorial about using the project with a particular javascript framework, or simply sharing the love on Twitter.

Other really great ways you can help move the community forward include helping answer questions on the [discussion group][google-group], or setting up an [email alert on StackOverflow][so-filter] so that you get notified of any new questions with the `django-rest-framework` tag.

When answering questions make sure to help future contributors find their way around by hyperlinking wherever possible to related threads and tickets, and include backlinks from those items if relevant. 

# Issues

It's really helpful if you make sure you address issues to the correct channel.  Usage questions should be directed to the [discussion group][google-group].  Feature requests, bug reports and other issues should be raised on the GitHub [issue tracker][issues].

Some tips on good issue reporting:

* When describing issues try to phrase your ticket in terms of the *behavior* you think needs changing rather than the *code* you think need changing.
* Search the issue list first for related items, and make sure you're running the latest version of REST framework before reporting an issue.
* If reporting a bug, then try to include a pull request with a failing test case.  This will help us quickly identify if there is a valid issue, and make sure that it gets fixed more quickly if there is one.



* TODO: Triage

# Development


* git clone & PYTHONPATH
* Pep8
* Recommend editor that runs pep8

### Pull requests

* Make pull requests early
* Describe branching

### Managing compatibility issues

* Describe compat module

# Testing

* Running the tests
* tox

# Documentation

The documentation for REST framework is built from the [Markdown][markdown] source files in [the docs directory][docs].

There are many great markdown editors that make working with the documentation really easy.  The [Mou editor for Mac][mou] is one such editor that comes highly recommended.

## Building the documentation

To build the documentation, simply run the `mkdocs.py` script.

    ./mkdocs.py

This will build the html output into the `html` directory.

You can build the documentation and open a preview in a browser window by using the `-p` flag.

    ./mkdocs.py -p

## Language style

Documentation should be in American English.  The tone of the documentation is very important - try to stick to a simple, plain, objective and well-balanced style where possible.

Some other tips:

* Keep paragraphs reasonably short.
* Use double spacing after the end of sentences.
* Don't use the abbreviations such as 'e.g..' but instead use long form, such as 'For example'.

## Markdown style

There are a couple of conventions you should follow when working on the documentation.

##### 1. Headers

Headers should use the hash style.  For example:

    ### Some important topic
    
The underline style should not be used.  **Don't do this:** 

    Some important topic
    ====================

##### 2. Links

Links should always use the reference style, with the referenced hyperlinks kept at the end of the document.

    Here is a link to [some other thing][other-thing].
    
    More text...
    
    [other-thing]: http://example.com/other/thing

This style helps keep the documentation source consistent and readable.

If you are hyperlinking to another REST framework document, you should use a relative link, and link to the `.md` suffix.  For example:

    [authentication]: ../api-guide/authentication.md

Linking in this style means you'll be able to click the hyperlink in your markdown editor to open the referenced document.  When the documentation is built, these links will be converted into regular links to HTML pages.

##### 3. Notes

If you want to draw attention to a note or warning, use a pair of enclosing lines, like so:

    ---
    
    **Note:** Make sure you do this thing.
    
    ---

# Third party packages

* Django reusable app

# Core committers

* Still use pull reqs
* Credits

[cite]: http://www.w3.org/People/Berners-Lee/FAQ.html
[github]: https://github.com/tomchristie/django-rest-framework
[django-packages]: https://www.djangopackages.com/grids/g/api/
[google-group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[so-filter]: http://stackexchange.com/filters/66475/rest-framework
[issues]: https://github.com/tomchristie/django-rest-framework/issues?state=open
[markdown]: http://daringfireball.net/projects/markdown/basics
[docs]: https://github.com/tomchristie/django-rest-framework/tree/master/docs
[mou]: http://mouapp.com/
