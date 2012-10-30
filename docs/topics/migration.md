# 2.0 Migration Guide

> Move fast and break things
>
> &mdash; Mark Zuckerberg, [the Hacker Way][cite].

REST framework 2.0 introduces a radical redesign of the core components, and a large number of backwards breaking changes.

### Serialization redesign.

REST framework's serialization and deserialization previously used a slightly odd combination of serializers for output, and Django Forms and Model Forms for input.  The serialization core has been completely redesigned based on work that was originally intended for Django core.

2.0's form-like serializers comprehensively address those issues, and are a much more flexible and clean solution to the problems around accepting both form-based and non-form based inputs.

### Generic views improved.

When REST framework 0.1 was released the current Django version was 1.2.  REST framework included a backport of the Django 1.3's upcoming `View` class, but it didn't take full advantage of the generic view implementations.

As of 2.0 the generic views in REST framework tie in much more cleanly and obviously with Django's existing codebase, and the mixin architecture is radically simplified.

### Cleaner request-response cycle.

REST framework 2.0's request-response cycle is now much less complex.

* Responses inherit from `SimpleTemplateResponse`, allowing rendering to be delegated to the response, not handled by the view.
* Requests extend the regular `HttpRequest`, allowing authentication and parsing to be delegated to the request, not handled by the view.

### Renamed attributes & classes.

Various attributes and classes have been renamed in order to fit in better with Django's conventions.

## Example: Blog Posts API

Let's take a look at an example from the REST framework 0.4 documentation...

    from djangorestframework.resources import ModelResource
    from djangorestframework.reverse import reverse
    from blogpost.models import BlogPost, Comment


    class BlogPostResource(ModelResource):
        """
        A Blog Post has a *title* and *content*, and can be associated
        with zero or more comments.
        """
        model = BlogPost
        fields = ('created', 'title', 'slug', 'content', 'url', 'comments')
        ordering = ('-created',)

        def url(self, instance):
            return reverse('blog-post',
                            kwargs={'key': instance.key},
                            request=self.request)

        def comments(self, instance):
            return reverse('comments',
                           kwargs={'blogpost': instance.key},
                           request=self.request)


    class CommentResource(ModelResource):
        """
        A Comment is associated with a given Blog Post and has a
        *username* and *comment*, and optionally a *rating*.
        """
        model = Comment
        fields = ('username', 'comment', 'created', 'rating', 'url', 'blogpost')
        ordering = ('-created',)

        def blogpost(self, instance):
            return reverse('blog-post',
                           kwargs={'key': instance.blogpost.key},
                           request=self.request)

There's a bit of a mix of concerns going on there.  We've got some information about how the data should be serialized, such as the `fields` attribute, and some information about how it should be retrieved from the database - the `ordering` attribute.

Let's start to re-write this for REST framework 2.0.

    from rest_framework import serializers

    class BlogPostSerializer(serializers.HyperlinkedModelSerializer):
        model = BlogPost
        fields = ('created', 'title', 'slug', 'content', 'url', 'comments')

    class CommentSerializer(serializers.HyperlinkedModelSerializer):
        model = Comment
        fields = ('username', 'comment', 'created', 'rating', 'url', 'blogpost')

[cite]: http://www.wired.com/business/2012/02/zuck-letter/
