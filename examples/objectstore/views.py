from django.conf import settings

from flywheel.resource import Resource
from flywheel.response import Response, status

import pickle
import os
import uuid

OBJECT_STORE_DIR = os.path.join(settings.MEDIA_ROOT, 'objectstore')


class ObjectStoreRoot(Resource):
    """Root of the Object Store API.
    Allows the client to get a complete list of all the stored objects, or to create a new stored object."""
    allowed_methods = anon_allowed_methods = ('GET', 'POST')

    def get(self, request, auth):
        """Return a list of all the stored object URLs."""
        keys = sorted(os.listdir(OBJECT_STORE_DIR))
        return [self.reverse(StoredObject, key=key) for key in keys]
    
    def post(self, request, auth, content):
        """Create a new stored object, with a unique key."""
        key = str(uuid.uuid1())
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        pickle.dump(content, open(pathname, 'wb'))
        return Response(status.HTTP_201_CREATED, content, {'Location': self.reverse(StoredObject, key=key)})
 
        
class StoredObject(Resource):
    """Represents a stored object.
    The object may be any picklable content."""
    allowed_methods = anon_allowed_methods = ('GET', 'PUT', 'DELETE')

    def get(self, request, auth, key):
        """Return a stored object, by unpickling the contents of a locally stored file."""
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        if not os.path.exists(pathname):
            return Response(status.HTTP_404_NOT_FOUND)
        return pickle.load(open(pathname, 'rb'))

    def put(self, request, auth, content, key):
        """Update/create a stored object, by pickling the request content to a locally stored file."""
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        pickle.dump(content, open(pathname, 'wb'))
        return content

    def delete(self, request, auth, key):
        """Delete a stored object, by removing it's pickled file."""
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        if not os.path.exists(pathname):
            return Response(status.HTTP_404_NOT_FOUND)
        os.remove(pathname)
