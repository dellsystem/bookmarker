from __future__ import unicode_literals

from django.apps import apps
from django.db import models
from django.utils import timezone


CATEGORIES = {
    'author': {
        'primary_model': ('books', 'Author'),
        'secondary_model': None,
        'icon': 'user',
        'noun': 'an author',
        'filter': True,
        'book_model': None,
    },
    'book': {
        'primary_model': ('books', 'Book'),
        'secondary_model': None,
        'icon': 'book',
        # TODO: differentiate between books & publications
        'noun': 'a book',
        'filter': True,
        'book_model': 'primary',
    },
    'tag': {
        'primary_model': ('books', 'Tag'),
        'secondary_model': None,
        'icon': 'tag',
        'noun': 'a tag',
        'filter': True,
        'book_model': None,
    },
    'note': {
        'primary_model': ('books', 'Note'),
        'secondary_model': ('books', 'Book'),
        'icon': 'sticky note',
        'noun': 'a note',
        'filter': True,
        'book_model': 'secondary',
    },
    'section': {
        'primary_model': ('books', 'Section'),
        'secondary_model': ('books', 'Book'),
        'icon': 'file alternate outline',
        # TODO: differentiate between chapters/articles/webpages?
        'noun': 'a section',
        'filter': True,
        'book_model': 'secondary',
    },
    'note_tag': {
        'primary_model': ('books', 'Note'),
        'secondary_model': ('books', 'Tag'),
        'icon': 'tags',
        'noun': 'a note tag',
        'filter': False,
        'book_model': None,
    },
    'term': {
        'primary_model': ('vocab', 'TermOccurrence'),
        'secondary_model': ('books', 'Book'),
        'icon': 'flag',  # TODO: this is wrong
        'noun': 'a vocabulary term',
        'filter': True,
        'book_model': 'secondary',
    }
}
CATEGORY_CHOICES = [
    (key, value['noun']) for key, value in CATEGORIES.items()
]
VERB_CHOICES = [
    ('added', 'added'),
    ('edited', 'edited'),
    ('deleted', 'deleted'),
]
# For filtering on the homepage.
FILTER_CATEGORIES = set(c for c in CATEGORIES if CATEGORIES[c]['filter'])


class Action(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    primary_id = models.IntegerField(blank=True, null=True)
    secondary_id = models.IntegerField(blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    verb = models.CharField(max_length=10)
    details = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']

    @property
    def display_template(self):
        return 'actions/{}.html'.format(self.category)

    @property
    def model_pic(self):
        # TODO: find the book somewhere in the hierarchy
        pass

    @property
    def icon(self):
        return CATEGORIES[self.category]['icon']

    @property
    def noun(self):
        return CATEGORIES[self.category]['noun']

    @property
    def primary_instance(self):
        app_label, model_name = CATEGORIES[self.category]['primary_model']
        model = apps.get_model(app_label=app_label, model_name=model_name)
        return model.objects.get(pk=self.primary_id)

    @property
    def secondary_instance(self):
        app_label, model_name = CATEGORIES[self.category]['secondary_model']
        model = apps.get_model(app_label=app_label, model_name=model_name)
        return model.objects.get(pk=self.secondary_id)

    @property
    def book_id(self):
        """Needs tests. Should be simplified w/o overengineering."""
        book_model = CATEGORIES[self.category]['book_model']
        if book_model is not None:
            if book_model == 'primary':
                return self.primary_id
            return self.secondary_id

    def __str__(self):
        return "{verb}: {noun} ({primary}, {secondary})".format(
            verb=self.verb,
            noun=self.noun,
            primary=self.primary_id,
            secondary=self.secondary_id,
        )
