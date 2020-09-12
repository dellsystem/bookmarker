from unittest.mock import patch, Mock
from django.test import TestCase

from books import goodreadstools


class TestGoodreadstools(TestCase):
    def setUp(self):
        self.client = Mock()
        self.redistools = Mock()

    def test_get_author_new(self):
        with patch.multiple(
            'books.goodreadstools',
            _client=self.client,
            redistools=self.redistools
        ):
            self.redistools.get_author.return_value = None
            self.client.find_author.return_value = None
            self.assertEqual(None, goodreadstools.get_author_by_name('new'))
            self.client.find_author.assert_called_once_with('new')

    def test_get_books_new(self):
        with patch.multiple(
            'books.goodreadstools',
            _client=self.client,
            redistools=self.redistools
        ):
            self.redistools.get_book.return_value = None
            self.client.search_books.return_value = []
            self.assertEqual([], goodreadstools.get_books_by_title('new'))
            self.client.search_books.assert_called_once_with('new')
