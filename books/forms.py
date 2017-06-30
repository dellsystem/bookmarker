from django import forms

from books.models import Author, Note, Section
from books.utils import roman_to_int


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        exclude = ['book']
        widgets = {
            'subject': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }

    def save(self, book):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        note = super(NoteForm, self).save(commit=False)

        note.book = book

        page = note.page_number
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

        note.page_number = page_number
        note.in_preface = in_preface
        note.section = note.determine_section()
        note.save()

        return note


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        exclude = ['book', 'authors']
        widgets = {
            'title': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }

    def save(self, book=None):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        section = super(SectionForm, self).save(commit=False)

        if book:
            section.book = book

        page = section.page_number
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

        if section.rating is None:
            section.rating = 0

        section.page_number = page_number
        section.in_preface = in_preface
        section.save()

        return section


class ArtefactAuthorForm(forms.Form):
    mode = forms.ChoiceField(
        choices=(
            ('default', 'Default'),
            ('custom', 'Custom'),
            ('none', 'None'),
        ),
        widget=forms.Select,
    )
    author = forms.ModelChoiceField(Author.objects.all(), required=False)
