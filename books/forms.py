from django import forms

from books.models import Author, Note, Section
from books.utils import roman_to_int


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        exclude = ['book', 'related_to']
        widgets = {
            'subject': forms.TextInput(attrs={'autofocus': 'autofocus'}),
            'comment': forms.Textarea(attrs={'rows': 5}),
            'tags': forms.SelectMultiple(
                attrs={
                    'class': 'ui fluid dropdown multi-select',
                }
            ),
        }

    def save(self, author_form, book=None):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        # This will blank out the authors. We need to add them back later.
        note = super(NoteForm, self).save(commit=False)
        if book:
            note.book = book
        else:
            # Clear the authors in case they've changed.
            note.authors.clear()

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
        self.save_m2m()

        if author_form.cleaned_data['mode'] == 'default':
            note.set_default_authors()
        elif author_form.cleaned_data['mode'] == 'custom':
            note.authors.add(*author_form.cleaned_data['authors'])

        return note


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        exclude = ['book', 'authors']
        widgets = {
            'title': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }

    def save(self, author_form, book=None):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        section = super(SectionForm, self).save(commit=False)

        if book:
            # We're creating the section for the first time.
            section.book = book
        else:
            # Clear the authors just in case they've changed.
            section.authors.clear()

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
        self.save_m2m()

        # Set the authors according to author_form. If the mode is 'none', we
        # don't need to do anything since the section has no authors by
        # default.
        if author_form.cleaned_data['mode'] == 'default':
            section.authors.add(*section.book.default_authors.all())
        elif author_form.cleaned_data['mode'] == 'custom':
                section.authors.add(*author_form.cleaned_data['authors'])

        # Check if there's another section by the same author and title.
        if section.authors.exists():
            other_section = Section.objects.filter(
                title=section.title,
                authors=section.authors.all(),
            ).exclude(
                pk=section.pk
            )
            if other_section.exists():
                section.related_to = other_section.get()
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
    authors = forms.ModelMultipleChoiceField(
        Author.objects.all(),
        required=False,
        widget=forms.widgets.SelectMultiple(
            attrs={
                'class': 'ui fluid search dropdown',
                'multiple': '',
        })
    )
