from __future__ import unicode_literals
import re

from django.db import models
from django.urls import reverse
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

    def __str__(self):
        return self.name


class Term(models.Model):
    text = models.CharField(max_length=100)
    definition = models.TextField()  # taken directly from an API
    language = LanguageField(default='en')
    highlights = models.TextField()  # words to highlight, separated by \n
    flagged = models.BooleanField(default=False)  # pretty words

    class Meta:
        ordering = ['text']

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return reverse('view_term', args=[str(self.id)])

    def get_highlights(self):
        return self.highlights.splitlines()


class TermOccurrence(SectionArtefact):
    term = models.ForeignKey(Term, on_delete=models.CASCADE,
        related_name='occurrences')
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
        related_name='terms')
    added = models.DateTimeField(auto_now_add=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE,
        blank=True, null=True, related_name='terms')
    quote = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    category = models.ForeignKey(TermCategory, on_delete=models.CASCADE)
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

    def get_absolute_url(self):
        return reverse('view_occurrence', args=[str(self.id)])

    def __str__(self):
        return "{term} in {book}".format(
            term=self.term.text,
            book=self.book.title,
        )

    def get_highlighted_quote(self):
        q = self.quote
        # For more efficient searching.
        q_search = self.quote.lower()
        q_search = q_search.replace('-', ' ').replace('"', '')
        q_search = q_search.replace("' ", ' ').replace(" '", ' ')
        highlights = self.term.highlights.splitlines()
        for h in highlights:
            if h in q_search:
                h = h.replace(' ', '[-" \']*')
                q = re.sub('(' + h + ')', r'<span class="highlight">\1</span>', q,
                           flags=re.I | re.UNICODE)

                # Only need to highlight on one term.
                break

        return markdown.markdown(q, extensions=['superscript'],
            smart_emphasis=False)
