from __future__ import unicode_literals
import operator

from django.db import models
from django.core.urlresolvers import reverse
from languages.fields import LanguageField

from .api import CLIENT


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
    completed_terms = models.BooleanField(default=False)
    completed_notes = models.BooleanField(default=False)
    completed_sections = models.BooleanField(default=False)
    summary = models.TextField(blank=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('view_book', args=[str(self.id)])

    @property
    def completed_summaries(self):
        """If there are sections, they must be complete AND each
        must have a summary. Otherwise, the book must have a summary."""
        if self.sections.count():
            return (
                self.completed_sections and
                not self.sections.filter(summary='').exists()
            )
        else:
            return len(self.summary) > 0

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

    def get_section_pages(self):
        section_pages = []
        for section in self.sections.all():
            try:
                page_number = int(section.first_page)
            except ValueError:
                continue

            section_pages.append((section, page_number))

        return sorted(section_pages, key=operator.itemgetter(1), reverse=True)


class Section(models.Model):
    book = models.ForeignKey(Book, related_name='sections')
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    first_page = models.CharField(max_length=5, blank=True)  # can be empty

    def __unicode__(self):
        s = self.title
        if self.first_page:
            s += ' - ' + self.first_page

        return s

    def get_absolute_url(self):
        return reverse('view_section', args=[str(self.id)])


class Note(models.Model):
    book = models.ForeignKey(Book, related_name='notes')
    added = models.DateTimeField(auto_now_add=True)
    page = models.CharField(max_length=5)  # Can be in Preface (e.g., vi)
    subject = models.CharField(max_length=100)
    quote = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    section = models.ForeignKey(Section, blank=True, null=True,
                                related_name='notes')
    section_title = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(Author, blank=True, null=True)  # original author - might be a quote

    def get_absolute_url(self):
        return reverse('view_note', args=[str(self.id)])

    def __unicode__(self):
        return "{subject} - {book}".format(
            subject=self.subject,
            book=self.book.title
        )

    class Meta:
        ordering = ['-added']
