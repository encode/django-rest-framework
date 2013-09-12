> To save HTTP requests, it may be convenient to send related documents along with the request.
>
> &mdash; [JSON API specification for Ember Data][cite].

# Writable nested serializers

Although flat data structures serve to properly delineate between the individual entities in your service, there are cases where it may be more appropriate or convenient to use nested data structures.

Nested data structures are easy enough to work with if they're read-only - simply nest your serializer classes and you're good to go.  However, there are a few more subtleties to using writable nested serializers, due to the dependancies between the various model instances, and the need to save or delete multiple instances in a single action.

## One-to-many data structures 

*Example of a **read-only** nested serializer.  Nothing complex to worry about here.*

	class ToDoItemSerializer(serializers.ModelSerializer):
	    class Meta:
	        model = ToDoItem
	        fields = ('text', 'is_completed')
	
	class ToDoListSerializer(serializers.ModelSerializer):
	    items = ToDoItemSerializer(many=True, read_only=True)
	
	    class Meta:
	        model = ToDoList
	        fields = ('title', 'items')

Some example output from our serializer.

    {
        'title': 'Leaving party preperations',
        'items': {
            {'text': 'Compile playlist', 'is_completed': True},
            {'text': 'Send invites', 'is_completed': False},
            {'text': 'Clean house', 'is_completed': False}            
        }
    }

Let's take a look at updating our nested one-to-many data structure.

### Validation errors

### Adding and removing items

### Making PATCH requests


[cite]: http://jsonapi.org/format/#url-based-json-api