from django.test import TestCase

from books.models import Book, BookDetails


class TestDeletingBook(TestCase):
    """When a book is deleted, the corresponding BookDetails object (if any)
    should be automatically deleted as well. This is not a built-in feature
    since Book has a OneToOneField for BookDetails, not the other way around.
    Possibly I should have set it up the other way. Who knows. In any case, I
    was able to work around this using a pre-delete signal."""
    def setUp(self):
        details = BookDetails.objects.create(
            goodreads_id='1234',
        )
        Book.objects.create(
            title="With Details",
            slug='with-details',
            details=details,
        )
        Book.objects.create(
            title="Without Details",
            slug='without-details',
        )

    def test_deleting_book_with_details(self):
        self.assertEqual(
            1,
            BookDetails.objects.count(),
            '1 BookDetails object should exist before deletion'
        )
        book = Book.objects.get(slug='with-details')
        book.delete()
        self.assertEqual(
            0,
            BookDetails.objects.count(),
            'No BookDetails objects should exist after deletion'
        )

    def test_deleting_book_without_details(self):
        # This is a book not from goodreads
        self.assertEqual(
            1,
            BookDetails.objects.count(),
            '1 BookDetails object should exist before deletion'
        )
        book = Book.objects.get(slug='without-details')
        book.delete()
        self.assertEqual(
            1,
            BookDetails.objects.count(),
            '1 BookDetails objects should still exist after deletion'
        )
