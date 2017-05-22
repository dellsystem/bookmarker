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


class BookManager(models.Manager):
    def create_book(self, goodreads_id):
        pass


class Book(models.Model):
    goodreads_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    image_url = models.URLField()
    link = models.URLField()
    authors = models.ManyToManyField(Author, related_name='books')
    language = LanguageField(default='en')
    objects = BookManager()
    is_processed = models.BooleanField(default=False)  # terms, notes, sections
    completed_sections = models.BooleanField(default=False)  # KEEP
    summary = models.TextField(blank=True)

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

    def get_latest_addition(self):
        if self.notes.count():
            latest_note = self.notes.latest('pk')
        else:
            latest_note = None

        if self.terms.count():
            latest_term = self.terms.latest('pk')
        else:
            latest_term = None

        if latest_note is None:
            if latest_term is None:
                return None
            else:
                return latest_term
        else:
            if latest_term is None:
                return latest_note
            else:
                if latest_term.added > latest_note.added:
                    return latest_term
                else:
                    return latest_note


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


class Section(PageArtefact):
    book = models.ForeignKey(Book, related_name='sections')
    author = models.ForeignKey(Author, related_name='sections', blank=True,
                               null=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ['-in_preface', 'page_number']

    def __unicode__(self):
        s = self.title
        if self.page_number:
            s += ' - %s' % self.get_page_display()

        return s

    def get_absolute_url(self):
        return reverse('view_section', args=[str(self.id)])

    def get_artefacts(self):
        """Returns a generator mixing notes and termoccurrences, ordered by
        page (only because PageArtefact defines a custom __cmp__ method)."""
        return merge(self.notes.all(), self.terms.all())


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


class Note(SectionArtefact):
    book = models.ForeignKey(Book, related_name='notes')
    added = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=100)
    quote = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    section = models.ForeignKey(Section, blank=True, null=True,
                                related_name='notes')
    author = models.ForeignKey(Author, blank=True, null=True)  # original author - might be a quote

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
