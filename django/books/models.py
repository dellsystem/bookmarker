from __future__ import unicode_literals
from heapq import merge
import operator

from django import forms
from django.core.urlresolvers import reverse
from django.db import models
from languages.fields import LanguageField

from .api import CLIENT
from .utils import int_to_roman, roman_to_int


class Author(models.Model):
    goodreads_id = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=100)
    link = models.URLField()
    slug = models.SlugField(null=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('view_author', args=[self.slug])

    def get_associated_books(self):
        """Get books the author is associated with, by section or directly."""
        books = set()
        # This needs to be optimised
        for details in self.books.all():
            books.add(details.book.pk)
        for section in self.sections.all():
            books.add(section.book_id)

        return books


class BookManager(models.Manager):
    def create_book(self, goodreads_id):
        pass


class RatingField(models.IntegerField):
    def __init__(self, min_value=0, max_value=5, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)


class BookDetails(models.Model):
    """Mostly from Goodreads, though the book doesn't have to be on GR."""
    goodreads_id = models.CharField(max_length=20, blank=True, null=True,
                                    db_index=True)
    link = models.URLField()
    has_pages = models.BooleanField(default=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    publisher = models.CharField(max_length=50, blank=True, null=True)
    num_pages = models.PositiveSmallIntegerField(blank=True, null=True)
    verified = models.BooleanField(default=False)  # the ISBN and related details
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    rating = RatingField(default=0, blank=True)
    # 'authors' is taken directly from GoodReads. Currently not used anywhere.
    authors = models.ManyToManyField(Author, blank=True, related_name='books')
    # The default authors set on a Section/Term/Note if they aren't specified.
    # If empty, then it's assumed that most sections are by different authors.
    default_authors = models.ManyToManyField(Author,
                                             blank=True,
                                             related_name='default_books')


class Book(models.Model):
    """If details are None, then it's a publication, not a book."""
    objects = BookManager()
    details = models.OneToOneField(BookDetails, on_delete=models.CASCADE,
                                   blank=True, null=True)
    title = models.CharField(max_length=255)
    language = LanguageField(default='en')
    image_url = models.URLField()
    is_processed = models.BooleanField(default=False, db_index=True)  # terms, notes, sections
    completed_sections = models.BooleanField(default=False)  # KEEP
    completed_read = models.BooleanField(default=True)
    summary = models.TextField(blank=True)
    comments = models.TextField(blank=True)  # temporary private notes
    source_url = models.URLField(blank=True)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('view_book', args=[self.slug])

    def has_pages(self):
        return self.details.has_pages if self.details else False


class PageNumberField(models.CharField):
    """In the database, it's a PositiveSmallIntegerField but I'm setting as a
    CharField for now to prevent the stupid validator from running too early"""
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 5
        super(models.CharField, self).__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        if not value.isdigit() and not roman_to_int(value):
            raise forms.ValidationError("Invalid page")

    def to_python(self, value):
        return value

    def formfield(self, **kwargs):
        return forms.CharField(**kwargs)


class PageArtefact(models.Model):
    """Inherited by Note, TermOccurrence, and Section."""
    in_preface = models.BooleanField()
    page_number = PageNumberField(default=1)

    class Meta:
        abstract = True

    def get_author_data(self):
        """Returns the mode and authors list (needed for
        populating ArtefactAuthorForm)"""
        authors = []

        if self.authors.count():
            if self.has_default_authors():
                mode = 'default'
            else:
                mode = 'custom'
                authors = self.authors.all()
        else:
            mode = 'none'

        return {
            'mode': mode,
            'authors': authors,
        }

    def __cmp__(self, other):
        """So we can compare notes with terms."""
        if self.in_preface:
            if other.in_preface:
                return cmp(self.page_number, other.page_number)
            else:
                return -1
        else:
            if other.in_preface:
                return 1
            else:
                return cmp(self.page_number, other.page_number)

    def get_page_display(self):
        if self.in_preface:
            return int_to_roman(self.page_number)
        else:
            return self.page_number


class Section(PageArtefact):
    book = models.ForeignKey(Book, related_name='sections')
    authors = models.ManyToManyField(Author, related_name='sections', blank=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    rating = RatingField(default=0, blank=True)
    source_url = models.URLField(blank=True)
    related_to = models.ForeignKey('self', blank=True, null=True)
    slug = models.SlugField(blank=True)  # only for link-worthy sections
    skipped = models.BooleanField(default=False, help_text='Not yet read')

    class Meta:
        ordering = ['-in_preface', 'page_number']

    def __unicode__(self):
        return "{book} - {title}".format(
            title=self.title,
            book=self.book.title
        )

    def get_absolute_url(self):
        return reverse('view_section', args=[str(self.id)])

    def get_artefacts(self):
        """Returns a generator mixing notes and termoccurrences, ordered by
        page (only because PageArtefact defines a custom __cmp__ method)."""
        return merge(
            self.notes.all().prefetch_related(
                'tags', 'authors', 'section__authors'
            ),
            self.terms.all().prefetch_related(
                'category', 'authors', 'term', 'section__authors',
            ),
        )

    def has_default_authors(self):
        details = self.book.details
        if details:
            return (
                set(a.pk for a in self.authors.all()) ==
                set(a.pk for a in details.default_authors.all())
            )
        else:
            return True

    def get_next(self):
        """Probably inefficient but the alternative is fairly complex so"""
        found_next = False
        for section in self.book.sections.all():
            if found_next:
                return section

            if section.pk == self.pk:
                found_next = True

    def get_previous(self):
        previous = None
        for section in self.book.sections.all():
            if section.pk == self.pk:
                return previous

            previous = section


class SectionArtefact(PageArtefact):
    """TermOccurrence and Note inherit from this. Section inherits from
    PageArtefact. Defines a determine_section() method that determines the
    correct section (if any) from the page number. Assumes that book is a
    defined field."""

    class Meta:
        abstract = True

    def determine_section(self):
        in_preface = self.in_preface
        sections = self.book.sections.filter(
            in_preface=in_preface,
            page_number__lte=self.page_number,
        )
        return sections.last()

    def has_default_authors(self):
        if self.section:
            return (
                set(a.pk for a in self.authors.all()) ==
                set(a.pk for a in self.section.authors.all())
            )
        else:
            details = self.book.details
            if details:
                return (
                    set(a.pk for a in details.authors.all()) ==
                    set(a.pk for a in details.default_authors.all())
                )
            else:
                return True

    def set_default_authors(self):
        if self.section:
            default_authors = self.section.authors.all()
        else:
            default_authors = self.book.details.default_authors.all()

        self.authors.add(*default_authors)


class NoteTag(models.Model):
    slug = models.SlugField(primary_key=True)
    description = models.TextField(blank=True)
    colour = models.CharField(max_length=20, unique=True)

    def __unicode__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('view_tag', args=[self.slug])


class Note(SectionArtefact):
    book = models.ForeignKey(Book, related_name='notes')
    added = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=100)
    quote = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    section = models.ForeignKey(Section, blank=True, null=True,
                                related_name='notes')
    # Should only be empty if the original author isn't in our database.
    # Will usually inherit from the Section, if present, or the book.
    authors = models.ManyToManyField(Author, blank=True, related_name='notes')
    tags = models.ManyToManyField(NoteTag, blank=True, related_name='notes')

    class Meta:
        ordering = ['-in_preface', 'page_number']

    @property
    def display_template(self):
        return 'note_display.html'

    def get_absolute_url(self):
        return reverse('view_note', args=[str(self.id)])

    def __unicode__(self):
        return "{subject} - {book}".format(
            subject=self.subject,
            book=self.book.title
        )
