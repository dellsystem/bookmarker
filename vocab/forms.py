from django import forms

from books.utils import roman_to_int
from .models import Term, TermOccurrence


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['text', 'definition', 'language', 'highlights']
        widgets = {
            'text': forms.TextInput(
                attrs={
                    'autofocus': 'autofocus',
                    'onkeypress': 'suggestTerms()',
                }
            ),
            'definition': forms.Textarea(attrs={'rows': 4}),
            'highlights': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super(TermForm, self).clean()
        term = cleaned_data.get('text')
        language = cleaned_data.get('language')
        definition = cleaned_data.get('definition')
        highlights = cleaned_data.get('highlights')

        # Make sure the highlights are specified and don't contain " or -.
        if not highlights:
            self.add_error('highlights', 'REQUIRED')
        else:
            if '-' in highlights or '"' in highlights:
                self.add_error('highlights', 'INVALID CHARS: - OR "')

        if not definition:
            term_exists = Term.objects.filter(
                text=term,
                language=language
            ).exists()
            if not term_exists:
                self.add_error('definition', 'Required')


class TermOccurrenceForm(forms.ModelForm):
    class Meta:
        model = TermOccurrence
        exclude = ['term', 'added', 'book', 'authors']
        widgets = {
            'quote': forms.Textarea(attrs={'rows': 3}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

    def save(self, author_form, book=None, term=None):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        occurrence = super(TermOccurrenceForm, self).save(commit=False)

        if book and term:
            occurrence.book = book
            occurrence.term = term
        else:
            occurrence.authors.clear()

        page = occurrence.page_number
        try:
            page_number = int(page)
        except ValueError:
            page_number = None

        in_preface = False
        if page_number is None:
            # Check if it's a roman numeral.
            page_number = roman_to_int(page)
            if page_number:
                in_preface = True

        occurrence.page_number = page_number
        occurrence.in_preface = in_preface
        occurrence.save()
        self.save_m2m()

        if author_form.cleaned_data['mode'] == 'default':
            occurrence.set_default_authors()
        elif author_form.cleaned_data['mode'] == 'custom':
            occurrence.authors.add(*author_form.cleaned_data['authors'])

        return occurrence
