from django.test import TestCase

from books.utils import roman_to_int

class TestCreateFromGoodreads(TestCase):
    def test_subsequent(self):
        self.assertEqual(roman_to_int('vii'), 7)

        self.assertEqual(roman_to_int('viii'), 8)

        self.assertEqual(roman_to_int('ix'), 9)

