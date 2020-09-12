from unittest.mock import patch, Mock
from django.test import TestCase
import json

from books import redistools


class TestRedistools(TestCase):
    def setUp(self):
        self.client = Mock()

    def test_get_author_new(self):
        with patch('books.redistools._client', self.client):
            self.client.get.return_value = None
            self.assertEquals(None, redistools.get_author('new'))
            self.client.get.assert_called_once_with('author:new')

    def test_get_author_existing(self):
        with patch('books.redistools._client', self.client):
            self.client.get.return_value = '{"foo": "bar"}'
            self.assertEquals(
                {'foo': 'bar'},
                redistools.get_author('existing')
            )
            self.client.get.assert_called_once_with('author:existing')

    def test_save_author(self):
        with patch('books.redistools._client', self.client):
            author_data = Mock(
                gid='1234',
                link='link',
                books=[Mock(title='Title 1'), Mock(title='Title 2')],
            )
            author_data.name = 'John Doe'  # can't be set as a kwarg on Mock
            redistools.save_author(author_data)
            self.client.set.assert_called_once_with('author:1234',
                json.dumps({
                    'id': '1234',
                    'name': 'John Doe',
                    'link': 'link',
                    'titles': 'Title 1, Title 2'
                })
            )

    def test_get_book_none(self):
        with patch('books.redistools._client', self.client):
            self.client.get.return_value = None
            self.assertEquals(None, redistools.get_book('new'))
            self.client.get.assert_called_once_with('book:new')

    def test_get_book_existing(self):
        with patch('books.redistools._client', self.client):
            self.client.get.return_value = '{"foo": "bar"}'
            self.assertEquals(
                {'foo': 'bar'},
                redistools.get_book('existing')
            )
            self.client.get.assert_called_once_with('book:existing')

    def test_save_book(self):
        with patch('books.redistools._client', self.client):
            mock_author = Mock(gid='999', link='link', books=[])
            mock_author.name = 'Naomi Klein'
            book_data = Mock(
                title='No Logo',
                gid='1234',
                link='link',
                format='Hardcover',
                publication_date=(None, None, 1999),  # happens sometimes
                isbn13='9780312421434',
                publisher='Random House',
                num_pages=None,  # also happens sometimes
                image_url='image',
                authors=[mock_author],
            )
            book = redistools.save_book(book_data)
            self.assertEquals(2, self.client.set.call_count)
            self.assertEquals({
                'id': '1234',
                'title': 'No Logo',
                'link': 'link',
                'format': 'Hardcover',
                'year': 1999,
                'isbn13': '9780312421434',
                'publisher': 'Random House',
                'num_pages': None,
                'image_url': 'image',
                'authors': [{
                    'id': '999',
                    'name': 'Naomi Klein',
                    'link': 'link',
                    'titles': 'No Logo',
                }]
            }, book)
