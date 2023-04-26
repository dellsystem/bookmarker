import datetime

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


class TestParseDate(TestCase):
    def test_invalid_input(self):
        self.assertEqual(None, goodreadstools._parse_date(''))

    def test_valid_input(self):
        self.assertEqual(
            datetime.date(2023, 2, 7),
            goodreadstools._parse_date('Feb 07, 2023')
        )
