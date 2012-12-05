# Tutorial 1: Serialization

## Introduction

This tutorial will cover creating a simple pastebin code highlighting Web API. Along the way it will introduce the various components that make up REST framework, and give you a comprehensive understanding of how everything fits together.

The tutorial is fairly in-depth, so you should probably get a cookie and a cup of your favorite brew before getting started.<!--  If you just want a quick overview, you should head over to the [quickstart] documentation instead. -->

---

**Note**: The final code for this tutorial is available in the [tomchristie/rest-framework-tutorial][repo] repository on GitHub.  There is also a sandbox version for testing, [available here][sandbox].

---

## Setting up a new environment

Before we do anything else we'll create a new virtual environment, using [virtualenv].  This will make sure our package configuration is kept nicely isolated from any other projects we're working on.

    :::bash
    mkdir ~/env
    virtualenv ~/env/tutorial
    source ~/env/tutorial/bin/activate

Now that we're inside a virtualenv environment, we can install our package requirements.

    pip install django
    pip install djangorestframework
    pip install pygments  # We'll be using this for the code highlighting

**Note:** To exit the virtualenv environment at any time, just type `deactivate`.  For more information see the [virtualenv documentation][virtualenv].

## Getting started

Okay, we're ready to get coding.
To get started, let's create a new project to work with.

    cd ~
    django-admin.py startproject tutorial
    cd tutorial

Once that's done we can create an app that we'll use to create a simple Web API.

    python manage.py startapp snippets

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

We'll also need to add our new `snippets` app and the `rest_framework` app to `INSTALLED_APPS`.

    INSTALLED_APPS = (
        ...
        'rest_framework',
        'snippets'
    )

We also need to wire up the root urlconf, in the `tutorial/urls.py` file, to include our snippet app's URLs.

    urlpatterns = patterns('',
        url(r'^', include('snippets.urls')),
    )

Okay, we're ready to roll.

## Creating a model to work with

For the purposes of this tutorial we're going to start by creating a simple `Snippet` model that is used to store code snippets.  Go ahead and edit the  `snippets` app's `models.py` file.

    from django.db import models
    from pygments.lexers import get_all_lexers
    from pygments.styles import get_all_styles
    
    LANGUAGE_CHOICES = sorted([(item[1][0], item[0]) for item in get_all_lexers()])
    STYLE_CHOICES = sorted((item, item) for item in list(get_all_styles()))
    
    
    class Snippet(models.Model):
        created = models.DateTimeField(auto_now_add=True)
        title = models.CharField(max_length=100, default='')
        code = models.TextField()
        linenos = models.BooleanField(default=False)
        language = models.CharField(choices=LANGUAGE_CHOICES,
                                    default='python',
                                    max_length=100)
        style = models.CharField(choices=STYLE_CHOICES,
                                 default='friendly',
                                 max_length=100)
       
        class Meta:
            ordering = ('created',)

Don't forget to sync the database for the first time.

    python manage.py syncdb

## Creating a Serializer class

The first thing we need to get started on our Web API is provide a way of serializing and deserializing the snippet instances into representations such as `json`.  We can do this by declaring serializers that work very similar to Django's forms.  Create a file in the `snippets` directory named `serializers.py` and add the following.

    from django.forms import widgets
    from rest_framework import serializers
    from snippets import models


    class SnippetSerializer(serializers.Serializer):
        pk = serializers.Field()  # Note: `Field` is an untyped read-only field.
        title = serializers.CharField(required=False,
                                      max_length=100)
        code = serializers.CharField(widget=widgets.Textarea,
                                     max_length=100000)
        linenos = serializers.BooleanField(required=False)
        language = serializers.ChoiceField(choices=models.LANGUAGE_CHOICES,
                                           default='python')
        style = serializers.ChoiceField(choices=models.STYLE_CHOICES,
                                        default='friendly')
    
        def restore_object(self, attrs, instance=None):
            """
            Create or update a new snippet instance.
            """
            if instance:
                # Update existing instance
                instance.title = attrs['title']
                instance.code = attrs['code']
                instance.linenos = attrs['linenos']
                instance.language = attrs['language']
                instance.style = attrs['style']
                return instance

            # Create new instance
            return models.Snippet(**attrs)

The first part of serializer class defines the fields that get serialized/deserialized.  The `restore_object` method defines how fully fledged instances get created when deserializing data.

We can actually also save ourselves some time by using the `ModelSerializer` class, as we'll see later, but for now we'll keep our serializer definition explicit.  

## Working with Serializers

Before we go any further we'll familiarize ourselves with using our new Serializer class.  Let's drop into the Django shell.

    python manage.py shell

Okay, once we've got a few imports out of the way, let's create a code snippet to work with.

    from snippets.models import Snippet
    from snippets.serializers import SnippetSerializer
    from rest_framework.renderers import JSONRenderer
    from rest_framework.parsers import JSONParser

    snippet = Snippet(code='print "hello, world"\n')
    snippet.save()

We've now got a few snippet instances to play with.  Let's take a look at serializing one of those instances.

    serializer = SnippetSerializer(snippet)
    serializer.data
    # {'pk': 1, 'title': u'', 'code': u'print "hello, world"\n', 'linenos': False, 'language': u'python', 'style': u'friendly'}

At this point we've translated the model instance into python native datatypes.  To finalize the serialization process we render the data into `json`.

    content = JSONRenderer().render(serializer.data)
    content
    # '{"pk": 1, "title": "", "code": "print \\"hello, world\\"\\n", "linenos": false, "language": "python", "style": "friendly"}'

Deserialization is similar.  First we parse a stream into python native datatypes... 

    import StringIO

    stream = StringIO.StringIO(content)
    data = JSONParser().parse(stream)

...then we restore those native datatypes into to a fully populated object instance.

    serializer = SnippetSerializer(data=data)
    serializer.is_valid()
    # True
    serializer.object
    # <Snippet: Snippet object>
    
Notice how similar the API is to working with forms.  The similarity should become even more apparent when we start writing views that use our serializer.

## Using ModelSerializers

Our `SnippetSerializer` class is replicating a lot of information that's also contained in the `Snippet` model.  It would be nice if we could keep out code a bit  more concise.

In the same way that Django provides both `Form` classes and `ModelForm` classes, REST framework includes both `Serializer` classes, and `ModelSerializer` classes.

Let's look at refactoring our serializer using the `ModelSerializer` class.
Open the file `snippets/serializers.py` again, and edit the `SnippetSerializer` class.

    class SnippetSerializer(serializers.ModelSerializer):
        class Meta:
            model = Snippet
            fields = ('id', 'title', 'code', 'linenos', 'language', 'style')



## Writing regular Django views using our Serializer

Let's see how we can write some API views using our new Serializer class.
For the moment we won't use any of REST framework's other features, we'll just write the views as regular Django views.

We'll start off by creating a subclass of HttpResponse that we can use to render any data we return into `json`.

Edit the `snippet/views.py` file, and add the following.

    from django.http import HttpResponse
    from django.views.decorators.csrf import csrf_exempt
    from rest_framework.renderers import JSONRenderer
    from rest_framework.parsers import JSONParser
    from snippets.models import Snippet
    from snippets.serializers import SnippetSerializer

    class JSONResponse(HttpResponse):
        """
        An HttpResponse that renders it's content into JSON.
        """
        def __init__(self, data, **kwargs):
            content = JSONRenderer().render(data)
            kwargs['content_type'] = 'application/json'
            super(JSONResponse, self).__init__(content, **kwargs)


The root of our API is going to be a view that supports listing all the existing snippets, or creating a new snippet.

    @csrf_exempt
    def snippet_list(request):
        """
        List all code snippets, or create a new snippet.
        """
        if request.method == 'GET':
            snippets = Snippet.objects.all()
            serializer = SnippetSerializer(snippets)
            return JSONResponse(serializer.data)

        elif request.method == 'POST':
            data = JSONParser().parse(request)
            serializer = SnippetSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JSONResponse(serializer.data, status=201)
            else:
                return JSONResponse(serializer.errors, status=400)

Note that because we want to be able to POST to this view from clients that won't have a CSRF token we need to mark the view as `csrf_exempt`.  This isn't something that you'd normally want to do, and REST framework views actually use more sensible behavior than this, but it'll do for our purposes right now. 

We'll also need a view which corresponds to an individual snippet, and can be used to retrieve, update or delete the snippet.

    @csrf_exempt
    def snippet_detail(request, pk):
        """
        Retrieve, update or delete a code snippet.
        """
        try:
            snippet = Snippet.objects.get(pk=pk)
        except Snippet.DoesNotExist:
            return HttpResponse(status=404)
 
        if request.method == 'GET':
            serializer = SnippetSerializer(snippet)
            return JSONResponse(serializer.data)
    
        elif request.method == 'PUT':
            data = JSONParser().parse(request)
            serializer = SnippetSerializer(snippet, data=data)
            if serializer.is_valid():
                serializer.save()
                return JSONResponse(serializer.data)
            else:
                return JSONResponse(serializer.errors, status=400)

        elif request.method == 'DELETE':
            snippet.delete()
            return HttpResponse(status=204)

Finally we need to wire these views up. Create the `snippets/urls.py` file:

    from django.conf.urls import patterns, url

    urlpatterns = patterns('snippets.views',
        url(r'^snippets/$', 'snippet_list'),
        url(r'^snippets/(?P<pk>[0-9]+)/$', 'snippet_detail')
    )

It's worth noting that there are a couple of edge cases we're not dealing with properly at the moment.  If we send malformed `json`, or if a request is made with a method that the view doesn't handle, then we'll end up with a 500 "server error" response.  Still, this'll do for now.

## Testing our first attempt at a Web API

**TODO: Describe using runserver and making example requests from console**

**TODO: Describe opening in a web browser and viewing json output**

## Where are we now

We're doing okay so far, we've got a serialization API that feels pretty similar to Django's Forms API, and some regular Django views.

Our API views don't do anything particularly special at the moment, beyond serving `json` responses, and there are some error handling edge cases we'd still like to clean up, but it's a functioning Web API.

We'll see how we can start to improve things in [part 2 of the tutorial][tut-2].

[quickstart]: quickstart.md
[repo]: https://github.com/tomchristie/rest-framework-tutorial
[sandbox]: http://restframework.herokuapp.com/
[virtualenv]: http://www.virtualenv.org/en/latest/index.html
[tut-2]: 2-requests-and-responses.md
