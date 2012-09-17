# Tutorial 3: Class Based Views

We can also write our API views using class based views, rather than function based views.  As we'll see this is a powerful pattern that allows us to reuse common functionality, and helps us keep our code [DRY][1].

## Rewriting our API using class based views

We'll start by rewriting the root view as a class based view.  All this involves is a little bit of refactoring.

    from blog.models import Comment
    from blog.serializers import CommentSerializer
    from django.http import Http404
    from djangorestframework.views import APIView
    from djangorestframework.response import Response
    from djangorestframework import status


    class CommentRoot(APIView):
        """
        List all comments, or create a new comment.
        """
        def get(self, request, format=None):
            comments = Comment.objects.all()
            serializer = CommentSerializer(instance=comments)
            return Response(serializer.data)

        def post(self, request, format=None):
            serializer = CommentSerializer(request.DATA)
            if serializer.is_valid():
                comment = serializer.object
                comment.save()
                return Response(serializer.serialized, status=status.HTTP_201_CREATED)
            return Response(serializer.serialized_errors, status=status.HTTP_400_BAD_REQUEST)

So far, so good.  It looks pretty similar to the previous case, but we've got better seperation between the different HTTP methods.  We'll also need to update the instance view. 

    class CommentInstance(APIView):
        """
        Retrieve, update or delete a comment instance.
        """

        def get_object(self, pk):
            try:
                return Comment.objects.get(pk=pk)
            except Comment.DoesNotExist:
                raise Http404

        def get(self, request, pk, format=None):
            comment = self.get_object(pk)
            serializer = CommentSerializer(instance=comment)
            return Response(serializer.data)

        def put(self, request, pk, format=None):
            comment = self.get_object(pk)
            serializer = CommentSerializer(request.DATA, instance=comment)
            if serializer.is_valid():
                comment = serializer.deserialized
                comment.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        def delete(self, request, pk, format=None):
            comment = self.get_object(pk)
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

That's looking good.  Again, it's still pretty similar to the function based view right now.

We'll also need to refactor our URLconf slightly now we're using class based views.

    from django.conf.urls import patterns, url
    from djangorestframework.urlpatterns import format_suffix_patterns
    from blogpost import views

    urlpatterns = patterns('',
        url(r'^$', views.CommentRoot.as_view()),
        url(r'^(?P<pk>[0-9]+)$', views.CommentInstance.as_view())
    )
    
    urlpatterns = format_suffix_patterns(urlpatterns)

Okay, we're done.  If you run the development server everything should be working just as before.

## Using mixins

One of the big wins of using class based views is that it allows us to easily compose reusable bits of behaviour.

The create/retrieve/update/delete operations that we've been using so far are going to be pretty simliar for any model-backed API views we create.  Those bits of common behaviour are implemented in REST framework's mixin classes.

Let's take a look at how we can compose our views by using the mixin classes.

    from blog.models import Comment
    from blog.serializers import CommentSerializer
    from djangorestframework import mixins
    from djangorestframework import generics

    class CommentRoot(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      generics.MultipleObjectBaseView):
        model = Comment
        serializer_class = CommentSerializer

        def get(self, request, *args, **kwargs):
            return self.list(request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            return self.create(request, *args, **kwargs)

We'll take a moment to examine exactly what's happening here - We're building our view using `MultipleObjectBaseView`, and adding in `ListModelMixin` and `CreateModelMixin`.

The base class provides the core functionality, and the mixin classes provide the `.list()` and `.create()` actions.  We're then explictly binding the `get` and `post` methods to the appropriate actions.  Simple enough stuff so far.

    class CommentInstance(mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          generics.SingleObjectBaseView):
        model = Comment
        serializer_class = CommentSerializer

        def get(self, request, *args, **kwargs):
            return self.retrieve(request, *args, **kwargs)

        def put(self, request, *args, **kwargs):
            return self.update(request, *args, **kwargs)

        def delete(self, request, *args, **kwargs):
            return self.destroy(request, *args, **kwargs)

Pretty similar.  This time we're using the `SingleObjectBaseView` class to provide the core functionality, and adding in mixins to provide the `.retrieve()`, `.update()` and `.destroy()` actions.

## Using generic class based views

Using the mixin classes we've rewritten the views to use slightly less code than before, but we can go one step further.  REST framework provides a set of already mixed-in generic views that we can use.

    from blog.models import Comment
    from blog.serializers import CommentSerializer
    from djangorestframework import generics


    class CommentRoot(generics.RootAPIView):
        model = Comment
        serializer_class = CommentSerializer


    class CommentInstance(generics.InstanceAPIView):
        model = Comment
        serializer_class = CommentSerializer

Wow, that's pretty concise.  We've got a huge amount for free, and our code looks like good, clean, idomatic Django.

Next we'll move onto [part 4 of the tutorial][2], where we'll take a look at how we can  customize the behavior of our views to support a range of authentication, permissions, throttling and other aspects.

[1]: http://en.wikipedia.org/wiki/Don't_repeat_yourself
[2]: 4-authentication-permissions-and-throttling.md
