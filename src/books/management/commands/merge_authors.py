from django.core.management.base import BaseCommand
from django.utils.six.moves import input

from books.models import *


class Command(BaseCommand):
    help = 'Merges the second author into the first.'

    def add_arguments(self, parser):
        parser.add_argument('first_author_id', type=int)
        parser.add_argument('second_author_id', type=int)

    def handle(self, *args, **options):
        first_author = Author.objects.get(pk=options['first_author_id'])
        second_author = Author.objects.get(pk=options['second_author_id'])
        print("Primary author: {}, {}".format(
            first_author.name, first_author.slug)
        )
        print("Secondary author: {}, {}".format(
            second_author.name, second_author.slug)
        )

        # Vocabulary terms
        print("{} terms to change".format(second_author.terms.count()))
        for term in second_author.terms.all():
            term.authors.add(first_author)
            term.authors.remove(second_author)

        # Notes
        print("{} notes to change".format(second_author.notes.count()))
        for note in second_author.notes.all():
            note.authors.add(first_author)
            note.authors.remove(second_author)

        # Sections
        print("{} sections to change".format(second_author.sections.count()))
        for section in second_author.sections.all():
            section.authors.add(first_author)
            section.authors.remove(second_author)

        # Default authors and authors
        # TODO: Merge the two (don't need both)
        print("{} books to change".format(second_author.books.count()))
        for book in second_author.books.all():
            book.authors.add(first_author)
            book.authors.remove(second_author)

        print("{} default books to change".format(second_author.default_books.count()))
        for book in second_author.default_books.all():
            book.default_authors.add(first_author)
            book.default_authors.remove(second_author)
