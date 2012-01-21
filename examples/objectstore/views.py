from django.conf import settings
from django.core.urlresolvers import reverse

from djangorestframework.views import View
from djangorestframework.response import Response
from djangorestframework import status

import pickle
import os
import uuid
import operator

OBJECT_STORE_DIR = os.path.join(settings.MEDIA_ROOT, 'objectstore')
MAX_FILES = 10

if not os.path.exists(OBJECT_STORE_DIR):
    os.makedirs(OBJECT_STORE_DIR)


def remove_oldest_files(dir, max_files):
    """
    Remove the oldest files in a directory 'dir', leaving at most 'max_files' remaining.
    We use this to limit the number of resources in the sandbox.
    """
    filepaths = [os.path.join(dir, file) for file in os.listdir(dir) if not file.startswith('.')]
    ctime_sorted_paths = [item[0] for item in sorted([(path, os.path.getctime(path)) for path in filepaths],
                                                     key=operator.itemgetter(1), reverse=True)]
    [os.remove(path) for path in ctime_sorted_paths[max_files:]]


class ObjectStoreRoot(View):
    """
    Root of the Object Store API.
    Allows the client to get a complete list of all the stored objects, or to create a new stored object.
    """

    def get(self, request):
        """
        Return a list of all the stored object URLs. (Ordered by creation time, newest first)
        """
        filepaths = [os.path.join(OBJECT_STORE_DIR, file) for file in os.listdir(OBJECT_STORE_DIR) if not file.startswith('.')]
        ctime_sorted_basenames = [item[0] for item in sorted([(os.path.basename(path), os.path.getctime(path)) for path in filepaths],
                                                             key=operator.itemgetter(1), reverse=True)]
        return [reverse('stored-object', kwargs={'key':key}) for key in ctime_sorted_basenames]

    def post(self, request):
        """
        Create a new stored object, with a unique key.
        """
        key = str(uuid.uuid1())
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        pickle.dump(self.CONTENT, open(pathname, 'wb'))
        remove_oldest_files(OBJECT_STORE_DIR, MAX_FILES)
        return Response(status.HTTP_201_CREATED, self.CONTENT, {'Location': reverse('stored-object', kwargs={'key':key})})


class StoredObject(View):
    """
    Represents a stored object.
    The object may be any picklable content.
    """

    def get(self, request, key):
        """
        Return a stored object, by unpickling the contents of a locally stored file.
        """
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        if not os.path.exists(pathname):
            return Response(status.HTTP_404_NOT_FOUND)
        return pickle.load(open(pathname, 'rb'))

    def put(self, request, key):
        """
        Update/create a stored object, by pickling the request content to a locally stored file.
        """
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        pickle.dump(self.CONTENT, open(pathname, 'wb'))
        return self.CONTENT

    def delete(self, request, key):
        """
        Delete a stored object, by removing it's pickled file.
        """
        pathname = os.path.join(OBJECT_STORE_DIR, key)
        if not os.path.exists(pathname):
            return Response(status.HTTP_404_NOT_FOUND)
        os.remove(pathname)
