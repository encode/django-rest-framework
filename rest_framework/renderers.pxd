#!/usr/bin/env python
# coding: utf-8

cimport cython

@cython.locals(media_type=unicode, format=unicode, charset=unicode, render_style=unicode)
cdef class BaseRenderer(object):
    """
    All renderers should extend this class, setting the `media_type`
    and `format` attributes, and override the `.render()` method.
    """

    @cython.locals(indent=int, separators=tuple)
    cpdef object render(self, dict data, accepted_media_type=?, renderer_context=?)

@cython.locals(compact=bool, ensure_ascii=bool, charset=unicode)
cdef class JSONRenderer(BaseRenderer):
    @cython.locals(base_media_type=unicode, params=dict)
    cpdef int get_indent(self, unicode accepted_media_type, dict renderer_context)

@cython.locals(callback_parameter=unicode, default_callback=unicode)
cdef class JSONPRenderer(JSONRenderer):
    cpdef unicode get_callback(self, dict renderer_context)
