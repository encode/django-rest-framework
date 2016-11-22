import unittest

from rest_framework.fields import is_simple_callable

try:
    import typings
except ImportError:
    typings = False


class TestIsSimpleCallable:
    def test_method(self):
        class Foo:
            @classmethod
            def classmethod(cls):
                pass

            def valid(self):
                pass

            def valid_kwargs(self, param='value'):
                pass

            def valid_vargs_kwargs(self, *args, **kwargs):
                pass

            def invalid(self, param):
                pass

        assert is_simple_callable(Foo.classmethod)

        # unbound methods
        assert not is_simple_callable(Foo.valid)
        assert not is_simple_callable(Foo.valid_kwargs)
        assert not is_simple_callable(Foo.valid_vargs_kwargs)
        assert not is_simple_callable(Foo.invalid)

        # bound methods
        assert is_simple_callable(Foo().valid)
        assert is_simple_callable(Foo().valid_kwargs)
        assert is_simple_callable(Foo().valid_vargs_kwargs)
        assert not is_simple_callable(Foo().invalid)

    def test_function(self):
        def simple():
            pass

        def valid(param='value', param2='value'):
            pass

        def valid_vargs_kwargs(*args, **kwargs):
            pass

        def invalid(param, param2='value'):
            pass

        assert is_simple_callable(simple)
        assert is_simple_callable(valid)
        assert is_simple_callable(valid_vargs_kwargs)
        assert not is_simple_callable(invalid)

    def test_4602_regression(self):
        from django.db import models

        class ChoiceModel(models.Model):
            choice_field = models.CharField(
                max_length=1, default='a',
                choices=(('a', 'A'), ('b', 'B')),
            )

            class Meta:
                app_label = 'tests'

        assert is_simple_callable(ChoiceModel().get_choice_field_display)

    @unittest.skipUnless(typings, 'requires python 3.5')
    def test_type_annotation(self):
        # The annotation will otherwise raise a syntax error in python < 3.5
        exec ("def valid(param: str='value'):  pass", locals())
        valid = locals()['valid']

        assert is_simple_callable(valid)
