from django import forms

from languages.fields import LanguageField

from books.models import Book, Author, Section
from .models import Term, TermOccurrence, TermCategory


class TermOccurrenceForm(forms.Form):
    term = forms.CharField(
        widget=forms.TextInput(attrs={'autofocus': 'autofocus'})
    )
    definition = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False
    )
    language = LanguageField().formfield()
    section = forms.ModelChoiceField(Section.objects.all())
    quote = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 4},
    ), required=False)
    comments = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 4},
    ), required=False)
    page = forms.CharField(max_length=5)
    category = forms.ModelChoiceField(TermCategory.objects.all())
    is_new = forms.BooleanField(required=False)
    is_defined = forms.BooleanField(required=False)
    author = forms.ModelChoiceField(Author.objects.all(), required=False)

    def clean(self):
        cleaned_data = super(TermOccurrenceForm, self).clean()
        term = cleaned_data.get('term')
        language = cleaned_data.get('language')
        definition = cleaned_data.get('definition')

        if not definition:
            term_exists = Term.objects.filter(
                text=term,
                language=language
            ).exists()
            if not term_exists:
                self.add_error('definition', 'Required')
