from django import forms

from books.models import Author, Note, Section, Book, BookDetails, Tag
from books.utils import roman_to_int, get_page_details


class MultipleSectionsForm(forms.Form):
    """For adding multiple sections at a time, in the format of
    [section title] [page number]
    for each line"""
    sections = forms.CharField(widget=forms.Textarea)

    def clean_sections(self):
        data = self.cleaned_data['sections']
        sections = []
        for line in data.splitlines():
            words = line.strip().split()
            if not words:
                # Skip empty lines and whitespace-only lines
                continue

            title = ' '.join(words[:-1])
            if not title:
                raise forms.ValidationError(
                    "Invalid line: {}".format(line)
                )

            try:
                page_number, in_preface = get_page_details(words[-1])
            except ValueError:
                raise forms.ValidationError(
                    "Invalid number: {}".format(words[-1])
            )

            sections.append({
                'title': title,
                'page_number': page_number,
                'in_preface': in_preface,
                'number': None,
            })

        # Check if any of the titles should be converted into section numbers.
        number = 1
        for i, section in enumerate(sections):
            # If the first 3 chapters don't have numbers, stop checking
            if number == 1 and i == 3:
                break

            number_string = '{}.'.format(number)
            if section['title'].startswith(number_string):
                section['title'] = section['title'][len(number_string):]
                section['number'] = number
                number += 1

        return sections


class SectionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.is_article():
            return u'{title} - {authors}'.format(
                title=obj.title,
                authors=', '.join(author.name for author in obj.authors.all())
            )

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


class PageNumberForm:
    """Inherit from this to ensure that the page number entered is no greater
    than the number of pages that the book supposedly has. Requires that
    self.book has been set (ideally in __init__)."""
    def clean_page_number(self):
        page_number = self.cleaned_data['page_number']
        if self.book.details and self.book.details.num_pages:
            if self.book.details and page_number.isdigit() and int(page_number) > self.book.details.num_pages:
                raise forms.ValidationError(
                    'This book has %d pages' % self.book.details.num_pages
                )

        return page_number


class NoteForm(forms.ModelForm, SectionChoiceForm, PageNumberForm):
    # This has to be here and not in SectionChoiceForm, otherwise the label
    # won't show up correctly (it'll default to __str__)
    section = SectionChoiceField(
        queryset=Section.objects.none(),
        required=False,
    )
    tags = forms.ModelMultipleChoiceField(
        Tag.objects.all().prefetch_related('category'),
        required=False,
        widget=forms.widgets.SelectMultiple(
            attrs={
                'class': 'ui fluid multiple search dropdown',
            }
        )
    )

    def __init__(self, book, *args, **kwargs):
        # Store the book so we can use it for populating the sections and also
        # for updating the Note in save() (but only if there isn't already a
        # book).
        self.book = book
        super(NoteForm, self).__init__(*args, **kwargs)
        self.fields['section'].queryset = book.sections.all()

        # Sections are required only for publications.
        if book.is_publication():
            self.fields['section'].required = True

    class Meta:
        model = Note
        exclude = ['book', 'related_to']
        widgets = {
            'subject': forms.TextInput(attrs={'autofocus': 'autofocus'}),
            'comment': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_subject(self):
        return self.cleaned_data['subject'].strip()

    def clean_quote(self):
        return self.cleaned_data['quote'].strip()

    def save(self, author_form, book=None):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        # This will blank out the authors. We need to add them back later.
        note = super(NoteForm, self).save(commit=False)
        if note.book_id:
            # Clear the authors in case they've changed.
            note.authors.clear()
        else:
            note.book = self.book

        page_number, in_preface = get_page_details(note.page_number)
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


class SectionForm(forms.ModelForm, PageNumberForm):
    class Meta:
        model = Section
        exclude = ['book', 'authors']
        widgets = {
            'title': forms.TextInput(attrs={'autofocus': 'autofocus'}),
            'related_to': forms.widgets.Select(
                attrs={
                    'class': 'ui fluid search dropdown',
                }
            )
        }

    def __init__(self, book, *args, **kwargs):
        self.book = book
        super(SectionForm, self).__init__(*args, **kwargs)
        if book.details is None:
            self.fields.pop('page_number')
            self.fields.pop('number')
        else:
            self.fields.pop('date')
        
        # If this section has a title, then show the related_to field.
        if self.instance and self.instance.title and self.instance.authors.exists():
            self.fields['related_to'].queryset = Section.objects.filter(authors=self.instance.authors.first()).exclude(book=self.book)
        else:
            self.fields.pop('related_to')


    def save(self, author_form):
        """Convert the string 'page' input into an integer (and set in_preface
        accordingly)."""
        section = super(SectionForm, self).save(commit=False)

        if section.book_id:
            # Clear the authors just in case they've changed.
            section.authors.clear()
        else:
            # We're creating the section for the first time.
            section.book = self.book

        page_number, in_preface = get_page_details(section.page_number)

        if section.rating is None:
            section.rating = 0

        section.page_number = page_number
        section.in_preface = in_preface
        section.save()
        self.save_m2m()

        # Set the authors according to author_form. If the mode is 'none', we
        # don't need to do anything since the section has no authors by
        # default.
        if author_form.cleaned_data['mode'] == 'default' and section.book.details:
            section.authors.add(*section.book.details.default_authors.all())
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


class BookDetailsForm(forms.ModelForm):
    class Meta:
        model = BookDetails
        exclude = ['book']
        widgets = {
            'default_authors': forms.widgets.SelectMultiple(
                attrs={
                    'class': 'ui fluid search dropdown',
                    'multiple': '',
                }
            ),
            'authors': forms.widgets.SelectMultiple(
                attrs={
                    'class': 'ui fluid search dropdown',
                    'multiple': '',
                }
            ),
            'goals': forms.widgets.SelectMultiple(
                attrs={
                    'class': 'ui fluid search dropdown',
                    'multiple': '',
                }
            ),
            'shelves': forms.Textarea(attrs={'rows': 1}),
            'review': forms.Textarea(attrs={'rows': 1}),
            'due_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'start_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'}),
            'end_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        }

    def save(self):
        details = super(BookDetailsForm, self).save(commit=False)
        if details.rating is None:
            details.rating = 0

        details.save()
        self.save_m2m()
        return details


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        exclude = ['details']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = '__all__'


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
