from django import forms

from books.models import Note, Section
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
        exclude = ['book']
        widgets = {
            'title': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }

    def save(self, book):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        section = super(SectionForm, self).save(commit=False)

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

        section.page_number = page_number
        section.in_preface = in_preface
        section.save()

        return section
