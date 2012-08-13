from django.conf import settings

from djangorestframework.reverse import reverse
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


def get_filename(key):
    """
    Given a stored object's key returns the file's path.
    """
    return os.path.join(OBJECT_STORE_DIR, key)


def get_file_url(key, request):
    """
    Given a stored object's key returns the URL for the object.
    """
    return reverse('stored-object', kwargs={'key': key}, request=request)


class ObjectStoreRoot(View):
    """
    Root of the Object Store API.
    Allows the client to get a complete list of all the stored objects, or to create a new stored object.
    """

    def get(self, request):
        """
        Return a list of all the stored object URLs. (Ordered by creation time, newest first)
        """
        filepaths = [os.path.join(OBJECT_STORE_DIR, file)
                     for file in os.listdir(OBJECT_STORE_DIR)
                     if not file.startswith('.')]
        ctime_sorted_basenames = [item[0] for item in sorted([(os.path.basename(path), os.path.getctime(path)) for path in filepaths],
                                                             key=operator.itemgetter(1), reverse=True)]
        return [get_file_url(key, request) for key in ctime_sorted_basenames]

    def post(self, request):
        """
        Create a new stored object, with a unique key.
        """
        key = str(uuid.uuid1())
        filename = get_filename(key)
        pickle.dump(self.CONTENT, open(filename, 'wb'))

        remove_oldest_files(OBJECT_STORE_DIR, MAX_FILES)
        url = get_file_url(key, request)
        return Response(status.HTTP_201_CREATED, self.CONTENT, {'Location': url})


class StoredObject(View):
    """
    Represents a stored object.
    The object may be any picklable content.
    """
    def get(self, request, key):
        """
        Return a stored object, by unpickling the contents of a locally
        stored file.
        """
        filename = get_filename(key)
        if not os.path.exists(filename):
            return Response(status.HTTP_404_NOT_FOUND)
        return pickle.load(open(filename, 'rb'))

    def put(self, request, key):
        """
        Update/create a stored object, by pickling the request content to a
        locally stored file.
        """
        filename = get_filename(key)
        pickle.dump(self.CONTENT, open(filename, 'wb'))
        return self.CONTENT

    def delete(self, request, key):
        """
        Delete a stored object, by removing it's pickled file.
        """
        filename = get_filename(key)
        if not os.path.exists(filename):
            return Response(status.HTTP_404_NOT_FOUND)
        os.remove(filename)
