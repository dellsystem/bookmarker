from django.test import TestCase

from books.models import Book, BookDetails


class TestCreateFromGoodreads(TestCase):
    def setUp(self):
        self.book = Book.objects.create_from_goodreads(
            goodreads_id='123',
            title='Book: Something',
            link='link',
            publication_date=('5', '14', '2009'),
            isbn13='9783531168050',
            publisher='Publisher',
            num_pages='335',
            image_url='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1356348356l/14700203._SX98_.jpg',
        )

    def test_long_title_with_colon(self):
        book2 = Book.objects.create_from_goodreads(
            goodreads_id='2',
            title='Portrait of the Manager as a Young Author: On Storytelling, Business, and Literature',
            link='link2',
            publication_date=('5', '14', '2009'),
            isbn13='9783531168051',
            publisher='Publisher',
            num_pages='100',
            image_url='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1356348356l/14700203._SX98_.jpg',
        )
        self.assertEqual(book2.slug, "portrait-of-the-manager-as-a-young-author")

    def test_long_title_without_colon(self):
        book2 = Book.objects.create_from_goodreads(
            goodreads_id='2',
            title='Portrait of the Manager as a Young Author, On Storytelling, Business, and Literature',
            link='link2',
            publication_date=('5', '14', '2009'),
            isbn13='9783531168051',
            publisher='Publisher',
            num_pages='100',
            image_url='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1356348356l/14700203._SX98_.jpg',
        )
        self.assertEqual(book2.slug, "portrait-of-the-manager-as-a-young-author-on")

    def test_long_title_without_spaces(self):
        book2 = Book.objects.create_from_goodreads(
            goodreads_id='2',
            title='Portrait of the Manager asayoungauthoronstorytellingbusinessandliterature',
            link='link2',
            publication_date=('5', '14', '2009'),
            isbn13='9783531168051',
            publisher='Publisher',
            num_pages='100',
            image_url='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1356348356l/14700203._SX98_.jpg',
        )
        self.assertEqual(book2.slug, "portrait-of-the-manager")

    def test_long_title_without_spaces_at_all(self):
        # Unlikely but you never know
        book2 = Book.objects.create_from_goodreads(
            goodreads_id='2',
            title='Portraitofthemanagerasayoungauthoronstorytellingbusinessandliterature',
            link='link2',
            publication_date=('5', '14', '2009'),
            isbn13='9783531168051',
            publisher='Publisher',
            num_pages='100',
            image_url='https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1356348356l/14700203._SX98_.jpg',
        )
        self.assertEqual(book2.slug, "portraitofthemanagerasayoungauthoronstorytellingbu")

    def test_initial_book(self):
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(BookDetails.objects.count(), 1)

        self.assertEqual(self.book.title, 'Book: Something')
        self.assertEqual(self.book.slug, 'book')
        self.assertEqual(self.book.image_url, 'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1356348356l/14700203._SY475_.jpg')

        self.assertEqual(self.book.details.year, 2009)
        self.assertEqual(self.book.details.num_pages, 335)
        self.assertEqual(self.book.details.goodreads_id, '123')

    def test_new_book_same_slug(self):
        new_book = Book.objects.create_from_goodreads(
            goodreads_id='999',
            title='Book: Something Else',
            link='link',
            publication_date=('1', '1', '2019'),
            isbn13='9783531168051',
            publisher='Publisher 2',
            num_pages='500',
            image_url='',
        )

        self.assertEqual(new_book.title, 'Book: Something Else')
        self.assertEqual(new_book.slug, 'book-2')
        self.assertEqual(new_book.image_url, '')

        self.assertEqual(new_book.details.year, 2019)
        self.assertEqual(new_book.details.num_pages, 500)
        self.assertEqual(new_book.details.goodreads_id, '999')

        # Now create a whole new book with again the same slug.
        third_book = Book.objects.create_from_goodreads(
            goodreads_id='100',
            title='Book: Once More',
            link='link2',
            publication_date=('1', '1', '2020'),
            isbn13='9783531168052',
            publisher='Publisher 3',
            num_pages='1000',
            image_url='',
        )

        self.assertEqual(third_book.title, 'Book: Once More')
        self.assertEqual(third_book.slug, 'book-3')
        self.assertEqual(third_book.image_url, '')

        self.assertEqual(third_book.details.year, 2020)
        self.assertEqual(third_book.details.num_pages, 1000)
        self.assertEqual(third_book.details.goodreads_id, '100')
