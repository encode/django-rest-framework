# Tutorial 1: Serialization

## Introduction

This tutorial will walk you through the building blocks that make up REST framework.   It'll take a little while to get through, but it'll give you a comprehensive understanding of how everything fits together.

## Setting up a new environment

Before we do anything else we'll create a new virtual environment, using [virtualenv].  This will make sure our package configuration is keep nicely isolated from any other projects we're working on.

    mkdir ~/env
    virtualenv --no-site-packages ~/env/tutorial
    source ~/env/tutorial/bin/activate

Now that we're inside a virtualenv environment, we can install our package requirements.

    pip install django
    pip install djangorestframework

**Note:** To exit the virtualenv environment at any time, just type `deactivate`.  For more information see the [virtualenv documentation][virtualenv].

## Getting started

Okay, we're ready to get coding.
To get started, let's create a new project to work with.

    django-admin.py startproject tutorial
    cd tutorial

Once that's done we can create an app that we'll use to create a simple Web API.

    python manage.py startapp blog

The simplest way to get up and running will probably be to use an `sqlite3` database for the tutorial.  Edit the `tutorial/settings.py` file, and set the default database `"ENGINE"` to `"sqlite3"`, and `"NAME"` to `"tmp.db"`.

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'tmp.db',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }

We'll also need to add our new `blog` app and the `djangorestframework` app to `INSTALLED_APPS`.

    INSTALLED_APPS = (
        ...
        'djangorestframework',
        'blog'
    )

We also need to wire up the root urlconf, in the `tutorial/urls.py` file, to include our blog views.

    urlpatterns = patterns('',
        url(r'^', include('blog.urls')),
    )

Okay, we're ready to roll.

## Creating a model to work with

For the purposes of this tutorial we're going to start by creating a simple `Comment` model that is used to store comments against a blog post.  Go ahead and edit the  `blog` app's `models.py` file.

    from django.db import models

    class Comment(models.Model):
        email = models.EmailField()
        content = models.CharField(max_length=200)
        created = models.DateTimeField(auto_now_add=True)

Don't forget to sync the database for the first time.

    python manage.py syncdb

## Creating a Serializer class

We're going to create a simple Web API that we can use to edit these comment objects with.  The first thing we need is a way of serializing and deserializing the objects into representations such as `json`.  We do this by declaring serializers, that work very similarly to Django's forms.  Create a file in the project named `serializers.py` and add the following.

    from blog import models
    from djangorestframework import serializers


    class CommentSerializer(serializers.Serializer):
        email = serializers.EmailField()
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()
        
        def restore_object(self, attrs, instance=None):
            """
            Create or update a new comment instance.
            """
            if instance:
                instance.email = attrs['email']
                instance.content = attrs['content']
                instance.created = attrs['created']
                return instance
            return models.Comment(**attrs)

The first part of serializer class defines the fields that get serialized/deserialized.  The `restore_object` method defines how fully fledged instances get created when deserializing data.

We can actually also save ourselves some time by using the `ModelSerializer` class, as we'll see later, but for now we'll keep our serializer definition explicit.  

## Working with Serializers

Before we go any further we'll familiarise ourselves with using our new Serializer class.  Let's drop into the Django shell.

    python manage.py shell

Okay, once we've got a few imports out of the way, we'd better create a few comments to work with.

    from blog.models import Comment
    from blog.serializers import CommentSerializer
    from djangorestframework.renderers import JSONRenderer
    from djangorestframework.parsers import JSONParser

    c1 = Comment(email='leila@example.com', content='nothing to say')
    c2 = Comment(email='tom@example.com', content='foo bar')
    c3 = Comment(email='anna@example.com', content='LOLZ!')
    c1.save()
    c2.save()
    c3.save()

We've now got a few comment instances to play with.  Let's take a look at serializing one of those instances.

    serializer = CommentSerializer(instance=c1)
    serializer.data
    # {'email': u'leila@example.com', 'content': u'nothing to say', 'created': datetime.datetime(2012, 8, 22, 16, 20, 9, 822774, tzinfo=<UTC>)}

At this point we've translated the model instance into python native datatypes.  To finalise the serialization process we render the data into `json`.

    stream = JSONRenderer().render(serializer.data)
    stream
    # '{"email": "leila@example.com", "content": "nothing to say", "created": "2012-08-22T16:20:09.822"}'

Deserialization is similar.  First we parse a stream into python native datatypes... 

    data = JSONParser().parse(stream)

...then we restore those native datatypes into to a fully populated object instance.

    serializer = CommentSerializer(data)
    serializer.is_valid()
    # True
    serializer.object
    # <Comment object at 0x10633b2d0>
    
Notice how similar the API is to working with forms.  The similarity should become even more apparent when we start writing views that use our serializer.

## Writing regular Django views using our Serializers

Let's see how we can write some API views using our new Serializer class.
We'll start off by creating a subclass of HttpResponse that we can use to render any data we return into `json`.

Edit the `blog/views.py` file, and add the following.

    from blog.models import Comment
    from blog.serializers import CommentSerializer
    from djangorestframework.renderers import JSONRenderer
    from djangorestframework.parsers import JSONParser
    from django.http import HttpResponse


    class JSONResponse(HttpResponse):
        """
        An HttpResponse that renders it's content into JSON.
        """

        def __init__(self, data, **kwargs):
            content = JSONRenderer().render(data)
            kwargs['content_type'] = 'application/json'
            super(JSONResponse, self).__init__(content, **kwargs)


The root of our API is going to be a view that supports listing all the existing comments, or creating a new comment.

    def comment_root(request):
        """
        List all comments, or create a new comment.
        """
        if request.method == 'GET':
            comments = Comment.objects.all()
            serializer = CommentSerializer(instance=comments)
            return JSONResponse(serializer.data)

        elif request.method == 'POST':
            data = JSONParser().parse(request)
            serializer = CommentSerializer(data)
            if serializer.is_valid():
                comment = serializer.object
                comment.save()
                return JSONResponse(serializer.data, status=201)
            else:
                return JSONResponse(serializer.error_data, status=400)

We'll also need a view which corrosponds to an individual comment, and can be used to retrieve, update or delete the comment.

    def comment_instance(request, pk):
        """
        Retrieve, update or delete a comment instance.
        """
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return HttpResponse(status=404)
 
        if request.method == 'GET':
            serializer = CommentSerializer(instance=comment)
            return JSONResponse(serializer.data)
    
        elif request.method == 'PUT':
            data = JSONParser().parse(request)
            serializer = CommentSerializer(data, instance=comment)
            if serializer.is_valid():
                comment = serializer.object
                comment.save()
                return JSONResponse(serializer.data)
            else:
                return JSONResponse(serializer.error_data, status=400)

        elif request.method == 'DELETE':
            comment.delete()
            return HttpResponse(status=204)

Finally we need to wire these views up, in the `tutorial/urls.py` file.

    from django.conf.urls import patterns, url

    urlpatterns = patterns('blog.views',
        url(r'^$', 'comment_root'),
        url(r'^(?P<pk>[0-9]+)$', 'comment_instance')
    )

It's worth noting that there's a couple of edge cases we're not dealing with properly at the moment.  If we send malformed `json`, or if a request is made with a method that the view doesn't handle, then we'll end up with a 500 "server error" response.  Still, this'll do for now.

## Testing our first attempt at a Web API

**TODO: Describe using runserver and making example requests from console**

**TODO: Describe opening in a web browser and viewing json output**

## Where are we now

We're doing okay so far, we've got a serialization API that feels pretty similar to Django's Forms API, and some regular Django views.

Our API views don't do anything particularly special at the moment, beyond serve `json` responses, and there's some error handling edge cases we'd still like to clean up, but it's a functioning Web API.

We'll see how we can start to improve things in [part 2 of the tutorial][tut-2].

[virtualenv]: http://www.virtualenv.org/en/latest/index.html
[tut-2]: 2-requests-and-responses.md