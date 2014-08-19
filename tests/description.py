# -- coding: utf-8 --

# Apparently there is a python 2.6 issue where docstrings of imported view classes
# do not retain their encoding information even if a module has a proper
# encoding declaration at the top of its source file. Therefore for tests
# to catch unicode related errors, a mock view has to be declared in a separate
# module.

from rest_framework.views import APIView


# test strings snatched from http://www.columbia.edu/~fdc/utf8/,
# http://winrus.com/utf8-jap.htm and memory
UTF8_TEST_DOCSTRING = (
    'zażółć gęślą jaźń'
    'Sîne klâwen durh die wolken sint geslagen'
    'Τη γλώσσα μου έδωσαν ελληνική'
    'யாமறிந்த மொழிகளிலே தமிழ்மொழி'
    'На берегу пустынных волн'
    'てすと'
    'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃ'
)


class ViewWithNonASCIICharactersInDocstring(APIView):
    __doc__ = UTF8_TEST_DOCSTRING
