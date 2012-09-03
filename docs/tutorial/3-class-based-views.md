# Tutorial 3: Using Class Based Views

We can also write our API views using class based views, rather than function based views.  As we'll see this is a powerful pattern that allows us to reuse common functionality, and helps us keep our code [DRY][1].

## Rewriting our API using class based views

We'll start by rewriting the root view as a class based view.  All this involves is a little bit of refactoring.

    from blog.models import Comment
    from blog.serializers import ComentSerializer
    from django.http import Http404
    from djangorestframework.views import APIView
    from djangorestframework.response import Response
    from djangorestframework.status import status

    class CommentRoot(APIView):
        """
        List all comments, or create a new comment.
        """ 
        def get(self, request, format=None):
            comments = Comment.objects.all()
            serializer = ComentSerializer(instance=comments)
            return Response(serializer.data)

        def post(self, request, format=None)
            serializer = ComentSerializer(request.DATA)
            if serializer.is_valid():
                comment = serializer.object
                comment.save()
                return Response(serializer.serialized, status=HTTP_201_CREATED)
            return Response(serializer.serialized_errors, status=HTTP_400_BAD_REQUEST)

     comment_root = CommentRoot.as_view()

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

        comment_instance = CommentInstance.as_view()

That's looking good.  Again, it's still pretty similar to the function based view right now.
Okay, we're done.  If you run the development server everything should be working just as before.

## Using mixins

One of the big wins of using class based views is that it allows us to easily compose reusable bits of behaviour.

The create/retrieve/update/delete operations that we've been using so far is going to be pretty simliar for any model-backed API views we create.  Those bits of common behaviour are implemented in REST framework's mixin classes.

We can compose those mixin classes, to recreate our existing API behaviour with less code.

    from blog.models import Comment
    from blog.serializers import CommentSerializer
    from djangorestframework import mixins, views

    class CommentRoot(mixins.ListModelQuerysetMixin,
                      mixins.CreateModelInstanceMixin,
                      views.BaseRootAPIView):
        model = Comment
        serializer_class = CommentSerializer

        get = list
        post = create

    class CommentInstance(mixins.RetrieveModelInstanceMixin,
                          mixins.UpdateModelInstanceMixin,
                          mixins.DestroyModelInstanceMixin,
                          views.BaseInstanceAPIView):
        model = Comment
        serializer_class = CommentSerializer

        get = retrieve
        put = update
        delete = destroy

## Reusing generic class based views

That's a lot less code than before, but we can go one step further still.  REST framework also provides a set of already mixed-in views.

    from blog.models import Comment
    from blog.serializers import CommentSerializer
    from djangorestframework import views

    class CommentRoot(views.RootAPIView):
        model = Comment
        serializer_class = CommentSerializer

    class CommentInstance(views.InstanceAPIView):
        model = Comment
        serializer_class = CommentSerializer

Wow, that's pretty concise.  We've got a huge amount for free, and our code looks like
good, clean, idomatic Django.

Next we'll move onto [part 4 of the tutorial][2], where we'll take a look at how we can  customize the behavior of our views to support a range of authentication, permissions, throttling and other aspects.

[1]: http://en.wikipedia.org/wiki/Don't_repeat_yourself
[2]: 4-authentication-permissions-and-throttling.md
