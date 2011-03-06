from django import forms

class MyForm(forms.Form):
    foo = forms.BooleanField(required=False)
    bar = forms.IntegerField(help_text='Must be an integer.')
    baz = forms.CharField(max_length=32, help_text='Free text.  Max length 32 chars.')
