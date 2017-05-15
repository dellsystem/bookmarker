import unittest

from django.core.management.base import NoArgsCommand
from vocab.models import TermOccurrence


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestChronology)
        unittest.TextTestRunner().run(suite)


class TestChronology(unittest.TestCase):
    def test_equality(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        for o in TermOccurrence.objects.exclude(quote=''):
            highlighted_quote = o.get_highlighted_quote()
            if '<span class="highlight">' not in highlighted_quote:
                self.fail(
                    u"Failed: looking for {highlights} in '{quote}'".format(
                        quote=o.quote,
                        highlights=o.term.highlights
                    )
                )
