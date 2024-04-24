from django import forms

from books.forms import SectionChoiceForm, SectionChoiceField, PageNumberForm
from books.models import Section
from books.utils import roman_to_int, get_page_details
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
                    'autocomplete': 'off',
                }
            ),
            'definition': forms.Textarea(attrs={'rows': 4}),
            'highlights': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_quote(self):
        return self.cleaned_data['quote'].strip()

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


class TermOccurrenceForm(forms.ModelForm, SectionChoiceForm, PageNumberForm):
    # This has to be here and not in SectionChoiceForm, otherwise the label
    # won't show up correctly (it'll default to __str__)
    section = SectionChoiceField(
        queryset=Section.objects.none(),
        required=False,
    )

    class Meta:
        model = TermOccurrence
        exclude = ['term', 'added', 'book', 'authors']
        widgets = {
            'quote': forms.Textarea(attrs={'rows': 3}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, book, *args, **kwargs):
        # Store the book so we can use it for populating the sections and also
        # for updating the Note in save() (but only if there isn't already a
        # book).
        self.book = book

        super(TermOccurrenceForm, self).__init__(*args, **kwargs)
        self.fields['section'].queryset = book.sections.all()

        # Sections are required only for publications.
        if book.is_publication():
            self.fields['section'].required = True

    def save(self, author_form, term=None):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        occurrence = super(TermOccurrenceForm, self).save(commit=False)

        if occurrence.book_id:
            occurrence.authors.clear()
        else:
            occurrence.book = self.book
            occurrence.term = term

        page_number, in_preface = get_page_details(occurrence.page_number)
        occurrence.page_number = page_number
        occurrence.in_preface = in_preface

        section = self.cleaned_data.get('section')
        if section:
            occurrence.section = section
        else:
            occurrence.section = occurrence.determine_section()

        occurrence.save()
        self.save_m2m()

        if author_form.cleaned_data['is_custom']:
            occurrence.authors.add(*author_form.cleaned_data['authors'])
        else:
            occurrence.set_default_authors()

        return occurrence
