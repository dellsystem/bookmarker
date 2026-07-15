import datetime
import os

from django.test import TestCase

from books import goodreadstools


class TestParseNumPages(TestCase):
    def test_invalid_input(self):
        self.assertEqual(None, goodreadstools._parse_num_pages('blah'))

    def test_valid_input(self):
        self.assertEqual(123, goodreadstools._parse_num_pages('123\np'))


class TestParseId(TestCase):
    def test_with_hyphen(self):
        self.assertEqual(
            '37941942',
            goodreadstools._parse_id('/book/show/37941942-the-flame')
        )

    def test_without_hyphen(self):
        self.assertEqual(
            '1188779',
            goodreadstools._parse_id('/book/show/1188779.Money')
        )


class TestRssParser(TestCase):
    def test_external_file(self):
        self.maxDiff = None
        rss_content = open(os.path.join(os.path.dirname(__file__), './goodreads_rss.xml')).read()
        books = goodreadstools._parse_rss(rss_content)
        self.assertEqual(books, [{
            'author_id': '',
            'author_slug': '',
            'title': 'The Mandarins',
            'author_name': 'Simone de Beauvoir',
            'id': '528763',
            'year': '1954',
            'link': 'https://www.goodreads.com/book/show/528763',
            'image_url': 'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1757105436l/528763.jpg',
            'rating': 5,
            'num_pages': 608,
            'isbn': '0393318834',
            'ignore_link_params': 'goodreads_id=528763&description=The+Mandarins',
            'shelves': 'fiction, new-favorites, women-and-their-dilemmas, worth-rereading',
            'review': 'OH MY GOD how did nobody tell me about this before. simone de beauvoir is astounding.',
            'book_params': 'title=The+Mandarins&id=528763&link=https%3A%2F%2Fwww.goodreads.com%2Fbook%2Fshow%2F528763&shelves=fiction%2C+new-favorites%2C+women-and-their-dilemmas%2C+worth-rereading&review=OH+MY+GOD+how+did+nobody+tell+me+about+this+before.+simone+de+beauvoir+is+astounding.&year=1954&isbn=0393318834&rating=5&num_pages=608&image_url=https%3A%2F%2Fi.gr-assets.com%2Fimages%2FS%2Fcompressed.photo.goodreads.com%2Fbooks%2F1757105436l%2F528763.jpg&author_name=Simone+de+Beauvoir&author_id=&author_slug='
        },
        {
            'author_id': '',
            'author_slug': '',
            'author_name': 'Notes from Below',
            'book_params': 'title=Shift+Patterns%3A+Experiments+in+Hospitality+Organising&id=221311408&link=https%3A%2F%2Fwww.goodreads.com%2Fbook%2Fshow%2F221311408&shelves=class-struggle&review=hell+yeah&year=&isbn=1739209079&rating=5&num_pages=87&image_url=https%3A%2F%2Fi.gr-assets.com%2Fimages%2FS%2Fcompressed.photo.goodreads.com%2Fbooks%2F1730989377l%2F221311408._SX318_.jpg&author_name=Notes+from+Below&author_id=&author_slug=',
            'link': 'https://www.goodreads.com/book/show/221311408',
            'id': '221311408',
            'ignore_link_params': 'goodreads_id=221311408&description=Shift+Patterns%3A+Experiments+in+Hospitality+Organising',
            'image_url': 'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1730989377l/221311408._SX318_.jpg',
            'isbn': '1739209079',
            'num_pages': 87,
            'rating': 5,
            'review': 'hell yeah',
            'shelves': 'class-struggle',
            'title': 'Shift Patterns: Experiments in Hospitality Organising',
            'year': ''
        }
    ])
