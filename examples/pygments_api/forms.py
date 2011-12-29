from django import forms

from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles

LEXER_CHOICES = sorted([(item[1][0], item[0]) for item in get_all_lexers()])
STYLE_CHOICES = sorted((item, item) for item in list(get_all_styles()))

class PygmentsForm(forms.Form):
    """A simple form with some of the most important pygments settings.
    The code to be highlighted can be specified either in a text field, or by URL.
    We do some additional form validation to ensure clients see helpful error responses."""

    code = forms.CharField(widget=forms.Textarea,
                           label='Code Text',
                           max_length=1000000,
                           help_text='(Copy and paste the code text here.)')
    title = forms.CharField(required=False,
                            help_text='(Optional)',
                            max_length=100)
    linenos = forms.BooleanField(label='Show Line Numbers',
                                 required=False)
    lexer = forms.ChoiceField(choices=LEXER_CHOICES,
                              initial='python')
    style = forms.ChoiceField(choices=STYLE_CHOICES,
                              initial='friendly')


