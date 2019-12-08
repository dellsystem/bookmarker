from django.core.management.base import BaseCommand
import unittest

from books.models import *


class Command(BaseCommand):
    def handle(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestBooksDatabase)
        unittest.TextTestRunner().run(suite)


class TestBooksDatabase(unittest.TestCase):
    def test_author_slugs(self):
        """
        Tests that all authors have slugs, and that they're all unique.
        """
        self.assertFalse(
            Author.objects.filter(slug=''),
            "There should be no authors with slug = ''",
        )
        self.assertFalse(
            Author.objects.filter(slug=None),
            "There should be no authors with slug = None",
        )
        slug_set = set()
        for author in Author.objects.all():
            if author.slug in slug_set:
                self.fail("Duplicate slug: {}".format(author.slug))
            slug_set.add(author.slug)

    def test_author_names(self):
        """
        Tests that all author names are different, and don't have extra
        characters."""
        self.assertFalse(
            Author.objects.filter(name=''),
            "There should be no authors with name = ''",
        )
        self.assertFalse(
            Author.objects.filter(name=None),
            "There should be no authors with name = None",
        )
        name_set = set()
        for author in Author.objects.all():
            if author.name in name_set:
                self.fail("Duplicate name: {}".format(author.name))
            name_set.add(author.name)

        for name in name_set:
            clean_name = name.strip().replace('  ', ' ')
            if clean_name != name:
                self.fail("Uncleaned name: {}".format(name))
