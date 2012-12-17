# Quickstart

We're going to create a simple API to allow admin users to view and edit the users and groups in the system.

Create a new Django project, and start a new app called `quickstart`.  Once you've set up a database and got everything synced and ready to go open up the app's directory and we'll get coding...

## Serializers

First up we're going to define some serializers in `quickstart/serializers.py` that we'll use for our data representations.

    from django.contrib.auth.models import User, Group, Permission
    from rest_framework import serializers
    
    
    class UserSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = User
            fields = ('url', 'username', 'email', 'groups')
    
    
    class GroupSerializer(serializers.HyperlinkedModelSerializer):
        permissions = serializers.ManySlugRelatedField(
            slug_field='codename',
            queryset=Permission.objects.all()
        )

        class Meta:
            model = Group
            fields = ('url', 'name', 'permissions')

Notice that we're using hyperlinked relations in this case, with `HyperlinkedModelSerializer`.  You can also use primary key and various other relationships, but hyperlinking is good RESTful design.

We've also overridden the `permission` field on the `GroupSerializer`.  In this case we don't want to use a hyperlinked representation, but instead use the list of permission codenames associated with the group, so we've used a `ManySlugRelatedField`, using the `codename` field for the representation.

## Views

Right, we'd better write some views then.  Open `quickstart/views.py` and get typing.

    from django.contrib.auth.models import User, Group
    from rest_framework import generics
    from rest_framework.decorators import api_view
    from rest_framework.reverse import reverse
    from rest_framework.response import Response
    from quickstart.serializers import UserSerializer, GroupSerializer
    
    
    @api_view(['GET'])
    def api_root(request, format=None):
        """
        The entry endpoint of our API.
        """
        return Response({
            'users': reverse('user-list', request=request),
            'groups': reverse('group-list', request=request),
        })
    
    
    class UserList(generics.ListCreateAPIView):
        """
        API endpoint that represents a list of users.
        """
        model = User
        serializer_class = UserSerializer
    
    
    class UserDetail(generics.RetrieveUpdateDestroyAPIView):
        """
        API endpoint that represents a single user.
        """
        model = User
        serializer_class = UserSerializer
    
    
    class GroupList(generics.ListCreateAPIView):
        """
        API endpoint that represents a list of groups.
        """
        model = Group
        serializer_class = GroupSerializer
    
    
    class GroupDetail(generics.RetrieveUpdateDestroyAPIView):
        """
        API endpoint that represents a single group.
        """
        model = Group
        serializer_class = GroupSerializer

Let's take a moment to look at what we've done here before we move on.  We have one function-based view representing the root of the API, and four class-based views which map to our database models, and specify which serializers should be used for representing that data.  Pretty simple stuff.

## URLs

Okay, let's wire this baby up.  On to `quickstart/urls.py`...

    from django.conf.urls import patterns, url, include
    from rest_framework.urlpatterns import format_suffix_patterns
    from quickstart.views import UserList, UserDetail, GroupList, GroupDetail
    

    urlpatterns = patterns('quickstart.views',
        url(r'^$', 'api_root'),
        url(r'^users/$', UserList.as_view(), name='user-list'),
        url(r'^users/(?P<pk>\d+)/$', UserDetail.as_view(), name='user-detail'),
        url(r'^groups/$', GroupList.as_view(), name='group-list'),
        url(r'^groups/(?P<pk>\d+)/$', GroupDetail.as_view(), name='group-detail'),
    )

    
    # Format suffixes
    urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])


    # Default login/logout views
    urlpatterns += patterns('',
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

There's a few things worth noting here.

Firstly the names `user-detail` and `group-detail` are important.  We're using the default hyperlinked relationships without explicitly specifying the view names, so we need to use names of the style `{modelname}-detail` to represent the model instance views.

Secondly, we're modifying the urlpatterns using `format_suffix_patterns`, to append optional `.json` style suffixes to our URLs.

Finally, we're including default login and logout views for use with the browsable API.  That's optional, but useful if your API requires authentication and you want to use the browseable API.

## Settings

We'd also like to set a few global settings.  We'd like to turn on pagination, and we want our API to only be accessible to admin users.

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

[image]: ../img/quickstart.png
[tutorial]: 1-serialization.md
[guide]: ../#api-guide
