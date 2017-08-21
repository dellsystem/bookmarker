from django import forms

from books.models import Author, Note, Section
from books.utils import roman_to_int


class SectionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return u'{title} ({page})'.format(
            title=obj.title,
            page=obj.page_number,
        )


class SectionChoiceForm:
    def clean(self):
        cleaned_data = super(NoteForm, self).clean()

        # Make sure the section-page combination is possible.
        section = cleaned_data.get('section')
        if section:
            # Assume that the page number is a valid one by this time. Just
            # check the bounds.
            page_number = int(cleaned_data.get('page_number'))
            if section.page_number > page_number:
                self.add_error('section', 'Page number too small for section')
            else:
                # The page number might be right. Make sure it doesn't belong
                # to a later section, if one exists.
                next_section = section.get_next()
                if next_section and next_section.page_number < page_number:
                    self.add_error('section', 'Page number too large for section')


class NoteForm(forms.ModelForm, SectionChoiceForm):
    # This has to be here and not in SectionChoiceForm, otherwise the label
    # won't show up correctly (it'll default to __unicode__)
    section = SectionChoiceField(
        queryset=Section.objects.none(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        # Store the book so we can use it for populating the sections and also
        # for updating the Note in save() (but only if there isn't already a
        # book).
        if kwargs.get('instance'):
            book = kwargs['instance'].book
            self.book = None
        else:
            book = kwargs.pop('book')
            self.book = book

        super(NoteForm, self).__init__(*args, **kwargs)
        self.fields['section'].queryset = book.sections.all()

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
        if self.book:
            note.book = self.book
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
        section = self.cleaned_data.get('section')
        if section:
            note.section = section
        else:
            note.section = note.determine_section()

        note.save()
        self.save_m2m()

        if author_form.cleaned_data['mode'] == 'default':
            note.set_default_authors()
        elif author_form.cleaned_data['mode'] == 'custom':
            note.authors.add(*author_form.cleaned_data['authors'])

        return note


class SectionForm(forms.ModelForm):
    related_to = forms.ModelChoiceField(
        queryset=Section.objects.all().select_related('book').order_by('book__title', 'title'),
        required=False,
    )

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
