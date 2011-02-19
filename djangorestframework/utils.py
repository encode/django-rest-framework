import re
import xml.etree.ElementTree as ET
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from django.core.urlresolvers import resolve
from django.conf import settings
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


#def admin_media_prefix(request):
#    """Adds the ADMIN_MEDIA_PREFIX to the request context."""
#    return {'ADMIN_MEDIA_PREFIX': settings.ADMIN_MEDIA_PREFIX}


def as_tuple(obj):
    """Given obj return a tuple"""
    if obj is None:
        return ()
    elif isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, tuple):
        return obj
    return (obj,)

  
def url_resolves(url):
    """Return True if the given URL is mapped to a view in the urlconf, False otherwise."""
    try:
        resolve(url)
    except:
        return False
    return True

# From piston
def coerce_put_post(request):
    """
    Django doesn't particularly understand REST.
    In case we send data over PUT, Django won't
    actually look at the data and load it. We need
    to twist its arm here.
    
    The try/except abominiation here is due to a bug
    in mod_python. This should fix it.
    """
    if request.method != 'PUT':
        return

    # Bug fix: if _load_post_and_files has already been called, for
    # example by middleware accessing request.POST, the below code to
    # pretend the request is a POST instead of a PUT will be too late
    # to make a difference. Also calling _load_post_and_files will result 
    # in the following exception:
    #   AttributeError: You cannot set the upload handlers after the upload has been processed.
    # The fix is to check for the presence of the _post field which is set 
    # the first time _load_post_and_files is called (both by wsgi.py and 
    # modpython.py). If it's set, the request has to be 'reset' to redo
    # the query value parsing in POST mode.
    if hasattr(request, '_post'):
        del request._post
        del request._files
    
    try:
        request.method = "POST"
        request._load_post_and_files()
        request.method = "PUT"
    except AttributeError:
        request.META['REQUEST_METHOD'] = 'POST'
        request._load_post_and_files()
        request.META['REQUEST_METHOD'] = 'PUT'
        
    request.PUT = request.POST

# From http://www.koders.com/python/fidB6E125C586A6F49EAC38992CF3AFDAAE35651975.aspx?s=mdef:xml
#class object_dict(dict):
#    """object view of dict, you can 
#    >>> a = object_dict()
#    >>> a.fish = 'fish'
#    >>> a['fish']
#    'fish'
#    >>> a['water'] = 'water'
#    >>> a.water
#    'water'
#    >>> a.test = {'value': 1}
#    >>> a.test2 = object_dict({'name': 'test2', 'value': 2})
#    >>> a.test, a.test2.name, a.test2.value
#    (1, 'test2', 2)
#    """
#    def __init__(self, initd=None):
#        if initd is None:
#            initd = {}
#        dict.__init__(self, initd)
#
#    def __getattr__(self, item):
#        d = self.__getitem__(item)
#        # if value is the only key in object, you can omit it
#        if isinstance(d, dict) and 'value' in d and len(d) == 1:
#            return d['value']
#        else:
#            return d
#
#    def __setattr__(self, item, value):
#        self.__setitem__(item, value)


# From xml2dict
class XML2Dict(object):

    def __init__(self):
        pass

    def _parse_node(self, node):
        node_tree = {}
        # Save attrs and text, hope there will not be a child with same name
        if node.text:
            node_tree = node.text
        for (k,v) in node.attrib.items():
            k,v = self._namespace_split(k, v)
            node_tree[k] = v
        #Save childrens
        for child in node.getchildren():
            tag, tree = self._namespace_split(child.tag, self._parse_node(child))
            if  tag not in node_tree: # the first time, so store it in dict
                node_tree[tag] = tree
                continue
            old = node_tree[tag]
            if not isinstance(old, list):
                node_tree.pop(tag)
                node_tree[tag] = [old] # multi times, so change old dict to a list       
            node_tree[tag].append(tree) # add the new one      

        return  node_tree


    def _namespace_split(self, tag, value):
        """
           Split the tag  '{http://cs.sfsu.edu/csc867/myscheduler}patients'
             ns = http://cs.sfsu.edu/csc867/myscheduler
             name = patients
        """
        result = re.compile("\{(.*)\}(.*)").search(tag)
        if result:
            value.namespace, tag = result.groups()    
        return (tag, value)

    def parse(self, file):
        """parse a xml file to a dict"""
        f = open(file, 'r')
        return self.fromstring(f.read()) 

    def fromstring(self, s):
        """parse a string"""
        t = ET.fromstring(s)
        unused_root_tag, root_tree = self._namespace_split(t.tag, self._parse_node(t))
        return root_tree


def xml2dict(input):
    return XML2Dict().fromstring(input)


# Piston:
class XMLEmitter():
    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement("list-item", {})
                self._to_xml(xml, item)
                xml.endElement("list-item")

        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)

        else:
            xml.characters(smart_unicode(data))

    def dict2xml(self, data):
        stream = StringIO.StringIO() 

        xml = SimplerXMLGenerator(stream, "utf-8")
        xml.startDocument()
        xml.startElement("root", {})

        self._to_xml(xml, data)

        xml.endElement("root")
        xml.endDocument()
        return stream.getvalue()

def dict2xml(input):
    return XMLEmitter().dict2xml(input)
