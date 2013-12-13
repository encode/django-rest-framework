# Quickstart

We're going to create a simple API to allow admin users to view and edit the users and groups in the system.

## Project setup

Create a new Django project named `tutorial`, then start a new app called `quickstart`.

    # Set up a new project
    django-admin.py startproject tutorial
    cd tutorial

    # Create a virtualenv to isolate our package dependencies locally
    virtualenv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`

    # Install Django and Django REST framework into the virtualenv
    pip install django
    pip install djangorestframework

    # Create a new app
    python manage.py startapp quickstart

Next you'll need to get a database set up and synced.  If you just want to use SQLite for now, then you'll want to edit your `tutorial/settings.py` module to include something like this:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'database.sql',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': ''
        }
    }

The run `syncdb` like so:

    python manage.py syncdb

Once you've set up a database and got everything synced and ready to go, open up the app's directory and we'll get coding...

## Serializers

First up we're going to define some serializers in `quickstart/serializers.py` that we'll use for our data representations.

    from django.contrib.auth.models import User, Group
    from rest_framework import serializers
    
    
    class UserSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = User
            fields = ('url', 'username', 'email', 'groups')
    
    
    class GroupSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = Group
            fields = ('url', 'name')

Notice that we're using hyperlinked relations in this case, with `HyperlinkedModelSerializer`.  You can also use primary key and various other relationships, but hyperlinking is good RESTful design.

## Views

Right, we'd better write some views then.  Open `quickstart/views.py` and get typing.

    from django.contrib.auth.models import User, Group
    from rest_framework import viewsets
    from quickstart.serializers import UserSerializer, GroupSerializer
    
    
    class UserViewSet(viewsets.ModelViewSet):
        """
        API endpoint that allows users to be viewed or edited.
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer
    
    
    class GroupViewSet(viewsets.ModelViewSet):
        """
        API endpoint that allows groups to be viewed or edited.
        """
        queryset = Group.objects.all()
        serializer_class = GroupSerializer

Rather than write multiple views we're grouping together all the common behavior into classes called `ViewSets`.

We can easily break these down into individual views if we need to, but using viewsets keeps the view logic nicely organized as well as being very concise.

Notice that our viewset classes here are a little different from those in the [frontpage example][readme-example-api], as they include `queryset` and `serializer_class` attributes, instead of a `model` attribute.

For trivial cases you can simply set a `model` attribute on the `ViewSet` class and the serializer and queryset will be automatically generated for you.  Setting the `queryset` and/or `serializer_class` attributes gives you more explicit control of the API behaviour, and is the recommended style for most applications.

## URLs

Okay, now let's wire up the API URLs.  On to `tutorial/urls.py`...

    from django.conf.urls import patterns, url, include
    from rest_framework import routers
    from quickstart import views

    router = routers.DefaultRouter()
    router.register(r'users', views.UserViewSet)
    router.register(r'groups', views.GroupViewSet)

    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browseable API.
    urlpatterns = patterns('',
        url(r'^', include(router.urls)),
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

Because we're using viewsets instead of views, we can automatically generate the URL conf for our API, by simply registering the viewsets with a router class.

Again, if we need more control over the API URLs we can simply drop down to using regular class based views, and writing the URL conf explicitly.

Finally, we're including default login and logout views for use with the browsable API.  That's optional, but useful if your API requires authentication and you want to use the browsable API.

## Settings

We'd also like to set a few global settings.  We'd like to turn on pagination, and we want our API to only be accessible to admin users.  The settings module will be in `tutorial/settings.py`

    INSTALLED_APPS = (
        ...
        'rest_framework',
    )

    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
        'PAGINATE_BY': 10
    }

Okay, we're done.

---

## Testing our API

We're now ready to test the API we've built.  Let's fire up the server from the command line.

    python ./manage.py runserver

We can now access our API, both from the command-line, using tools like `curl`...

    bash: curl -H 'Accept: application/json; indent=4' -u admin:password http://127.0.0.1:8000/users/ 
    {
        "count": 2, 
        "next": null, 
        "previous": null, 
        "results": [
            {
                "email": "admin@example.com", 
                "groups": [], 
                "url": "http://127.0.0.1:8000/users/1/", 
                "username": "admin"
            }, 
            {
                "email": "tom@example.com", 
                "groups": [                ], 
                "url": "http://127.0.0.1:8000/users/2/", 
                "username": "tom"
            }
        ]
    }

Or directly through the browser...

![Quick start image][image]

Great, that was easy!

If you want to get a more in depth understanding of how REST framework fits together head on over to [the tutorial][tutorial], or start browsing the [API guide][guide].

[readme-example-api]: ../#example
[image]: ../img/quickstart.png
[tutorial]: 1-serialization.md
[guide]: ../#api-guide
