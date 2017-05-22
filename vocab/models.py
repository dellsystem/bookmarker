from __future__ import unicode_literals
import re

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from languages.fields import LanguageField
import markdown

from books.models import Book, Author, Section, SectionArtefact


class TermCategory(models.Model):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100)
    confidence = models.PositiveSmallIntegerField(unique=True)  # 0 to 100

    class Meta:
        verbose_name_plural = 'Term categories'
        ordering = ['confidence']

    def __unicode__(self):
        return self.name


class Term(models.Model):
    text = models.CharField(max_length=100)
    definition = models.TextField()  # taken directly from an API
    language = LanguageField(default='en')
    highlights = models.TextField()  # words to highlight, separated by /

    class Meta:
        ordering = ['text']

    def __unicode__(self):
        return self.text

    def get_absolute_url(self):
        return reverse('view_term', args=[str(self.id)])

    def get_highlights(self):
        return self.highlights.split('/')


class TermOccurrence(SectionArtefact):
    term = models.ForeignKey(Term, related_name='occurrences')
    book = models.ForeignKey(Book, related_name='terms')
    added = models.DateTimeField(auto_now_add=True)
    section = models.ForeignKey(Section, blank=True, null=True,
                                related_name='terms')
    quote = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    category = models.ForeignKey(TermCategory)
    is_new = models.BooleanField()
    is_defined = models.BooleanField()  # if the author expects unfamiliarity
    # Should only be empty if the original author isn't in our database.
    # Will usually inherit from the Section, if present, or the book.
    authors = models.ManyToManyField(Author, blank=True, related_name='terms')

    class Meta:
        ordering = ['-in_preface', 'page_number']

    @property
    def display_template(self):
        return 'term_display.html'

    def save(self, *args, **kwargs):
        self.section = self.determine_section()
        super(TermOccurrence, self).save(*args, **kwargs)

    def __unicode__(self):
        return "{term} in {book}".format(
            term=self.term.text,
            book=self.book.title,
        )

    def get_highlighted_quote(self):
        q = self.quote
        q_lower = self.quote.lower()  # for more efficient (?) searching
        highlights = self.term.highlights.split('/')
        for h in highlights:
            if h in q_lower:
                q = re.sub('(' + h + ')', r'<span class="highlight">\1</span>', q,
                           flags=re.I)

                # Only need to highlight on one term.
                break

        return markdown.markdown(q)
