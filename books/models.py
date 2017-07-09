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
    goodreads_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    link = models.URLField()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('view_author', args=[str(self.id)])

    def get_associated_books(self):
        """Get books the author is associated with, by section, by note, by
        term, or as a direct author."""
        books = set()
        for book in self.books.all():
            books.add(book)
        for section in self.sections.all():
            books.add(section.book)
        for note in self.notes.all():
            books.add(note.book)
        for term in self.terms.all():
            books.add(term.book)
        return books


class BookManager(models.Manager):
    def create_book(self, goodreads_id):
        pass


class Book(models.Model):
    goodreads_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    image_url = models.URLField()
    link = models.URLField()
    authors = models.ManyToManyField(Author, related_name='books')
    # The default authors set on a Section/Term/Note if they aren't specified.
    # If empty, then it's assumed that most sections are by different authors.
    default_authors = models.ManyToManyField(Author,
                                             blank=True,
                                             related_name='default_books')
    language = LanguageField(default='en')
    objects = BookManager()
    is_processed = models.BooleanField(default=False)  # terms, notes, sections
    completed_sections = models.BooleanField(default=False)  # KEEP
    completed_read = models.BooleanField(default=True)
    summary = models.TextField(blank=True)
    comments = models.TextField(blank=True)  # temporary private notes
    source_url = models.URLField(blank=True)
    has_pages = models.BooleanField(default=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('view_book', args=[str(self.id)])

    def get_summary_percent(self):
        num_sections = self.sections.count()
        if num_sections:
            return self.sections.exclude(summary='').count() * 100 / num_sections
        else:
            # 100% if the book summary is filled in. 0% otherwise.
            if self.summary:
                return 100
            else:
                return 0


class PageNumberField(models.PositiveSmallIntegerField):
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
    page_number = PageNumberField()

    class Meta:
        abstract = True

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


class RatingField(models.IntegerField):
    def __init__(self, min_value=0, max_value=5, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)


class Section(PageArtefact):
    book = models.ForeignKey(Book, related_name='sections')
    authors = models.ManyToManyField(Author, related_name='sections', blank=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    rating = RatingField(default=0, blank=True)
    source_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-in_preface', 'page_number']

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('view_section', args=[str(self.id)])

    def get_artefacts(self):
        """Returns a generator mixing notes and termoccurrences, ordered by
        page (only because PageArtefact defines a custom __cmp__ method)."""
        return merge(self.notes.all(), self.terms.all())

    def has_default_authors(self):
        return (
            set(self.authors.values_list('pk')) ==
            set(self.book.default_authors.values_list('pk'))
        )


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
                set(self.authors.values_list('pk')) ==
                set(self.section.authors.values_list('pk'))
            )
        else:
            return (
                set(self.authors.values_list('pk')) ==
                set(self.book.default_authors.values_list('pk'))
            )

    def set_default_authors(self):
        if self.section:
            default_authors = self.section.authors.all()
        else:
            default_authors = self.book.default_authors.all()

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

    def save(self, *args, **kwargs):
        self.section = self.determine_section()
        super(Note, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('view_note', args=[str(self.id)])

    def __unicode__(self):
        return "{subject} - {book}".format(
            subject=self.subject,
            book=self.book.title
        )
