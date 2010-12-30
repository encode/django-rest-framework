from django import forms

class ExampleForm(forms.Form):
    title = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    valid = forms.BooleanField(required=False)
