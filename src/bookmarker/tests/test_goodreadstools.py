import datetime

from django.test import TestCase

from books import goodreadstools


class TestParseImageUrl(TestCase):
    def test_75(self):
        # Real data
        self.assertEqual(
            'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1665649420l/60644838._SY475_.jpg',
            goodreadstools._parse_image_url('https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1665649420l/60644838._SY75_.jpg')
        )

    def test_475(self):
        # Fake data - already done, doesn't need to change
        self.assertEqual(
            'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1599047628l/55155120._SY475_.jpg',
            goodreadstools._parse_image_url('https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1599047628l/55155120._SY475_.jpg')
        )

    def test_50(self):
        # Real data. idk why it's sometimes SX and sometimes SY.
        self.assertEqual(
            'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1599047628l/55155120._SY475_.jpg',
            goodreadstools._parse_image_url('https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1599047628l/55155120._SX50_.jpg')
        )


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


class TestParseDate(TestCase):
    def test_invalid_input(self):
        self.assertEqual(None, goodreadstools._parse_date(''))

    def test_valid_input(self):
        self.assertEqual(
            datetime.date(2023, 2, 7),
            goodreadstools._parse_date('Feb 07, 2023')
        )
