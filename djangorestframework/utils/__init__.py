from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from django.core.urlresolvers import resolve
from django.conf import settings

from djangorestframework.compat import StringIO

import re
import xml.etree.ElementTree as ET


#def admin_media_prefix(request):
#    """Adds the ADMIN_MEDIA_PREFIX to the request context."""
#    return {'ADMIN_MEDIA_PREFIX': settings.ADMIN_MEDIA_PREFIX}

from mediatypes import media_type_matches, is_form_media_type
from mediatypes import add_media_type_param, get_media_type_params, order_by_precedence

MSIE_USER_AGENT_REGEX = re.compile(r'^Mozilla/[0-9]+\.[0-9]+ \([^)]*; MSIE [0-9]+\.[0-9]+[a-z]?;[^)]*\)(?!.* Opera )')

def as_tuple(obj):
    """
    Given an object which may be a list/tuple, another object, or None,
    return that object in list form.

    IE:
    If the object is already a list/tuple just return it.
    If the object is not None, return it in a list with a single element.
    If the object is None return an empty list.
    """
    if obj is None:
        return ()
    elif isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, tuple):
        return obj
    return (obj,)

  
def url_resolves(url):
    """
    Return True if the given URL is mapped to a view in the urlconf, False otherwise.
    """
    try:
        resolve(url)
    except:
        return False
    return True


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
class XMLRenderer():
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
    return XMLRenderer().dict2xml(input)
