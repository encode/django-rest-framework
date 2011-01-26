from django import forms

from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles

import httplib2 as httplib


LEXER_CHOICES = sorted([(item[1][0], item[0]) for item in get_all_lexers()])
STYLE_CHOICES = sorted((item, item) for item in list(get_all_styles()))


class PygmentsForm(forms.Form):
    """A simple form with some of the most important pygments settings.
    The code to be highlighted can be specified either in a text field, or by URL.
    We do some additional form validation to ensure clients see helpful error responses."""

    code_url = forms.URLField(required=False, label='Code URL',
                              help_text='eg. https://bitbucket.org/tomchristie/flywheel/raw/cc266285d879/flywheel/resource.py')
    code_text = forms.CharField(widget=forms.Textarea, required=False, label='Code Text',
                                help_text='Either supply a URL for the code to be highlighted or copy and paste the code text here.')
    title = forms.CharField(required=False, help_text='(Optional)')
    linenos = forms.BooleanField(label='Show Line Numbers', required=False)
    lexer = forms.ChoiceField(choices=LEXER_CHOICES, initial='python')
    style = forms.ChoiceField(choices=STYLE_CHOICES, initial='friendly')

    
    def clean_code_url(self):
        """Custom field validation.
        Ensure that code URLs really are valid, and return the content they point to in the cleaned_data,
        rather than returning the URL itself."""
        cleaned_data = self.cleaned_data
        url = cleaned_data.get('code_url')
        if not url:
            return ''

        try:
            http = httplib.Http('.cache')
            resp, content = http.request(url)
        except:
            raise forms.ValidationError('The URL supplied cannot be reached')

        if int(resp.status/100) != 2:
            raise forms.ValidationError('The URL supplied does not return successfully')
        if not content:
            raise forms.ValidationError('The URL supplied returns no content')
        
        return content
        

    def clean(self):
        """Custom form validation.
        Ensure that only one of code_url and code_text is set, and return the content of whichever is set in 'code'."""
        cleaned_data = self.cleaned_data
        code_url = cleaned_data.get('code_url')
        code_text = cleaned_data.get('code_text')

        if not code_url and not code_text:
            raise forms.ValidationError('Either the URL or the code text must be supplied')
        if code_url and code_text:
            raise forms.ValidationError('You may not specify both the URL and the code text')

        if code_url:
            cleaned_data['code'] = code_url
            del cleaned_data['code_url']
        else:
            cleaned_data['code'] = code_text
            del cleaned_data['code_text']

        return cleaned_data

