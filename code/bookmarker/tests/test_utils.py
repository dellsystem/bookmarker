from django.test import TestCase

from books.utils import roman_to_int, get_page_details


class TestRomanToInt(TestCase):
    def test_subsequent(self):
        self.assertEqual(roman_to_int('vii'), 7)

        self.assertEqual(roman_to_int('viii'), 8)

        self.assertEqual(roman_to_int('ix'), 9)

    def test_invalid(self):
        self.assertEqual(roman_to_int('oxox'), 0)


class TestPageDetails(TestCase):
    def test_roman_numerals(self):
        self.assertEqual(get_page_details('vii'), (7, True))
        self.assertEqual(get_page_details('viii'), (8, True))
        self.assertEqual(get_page_details('i'), (1, True))

    def test_non_roman_numerals(self):
        self.assertEqual(get_page_details('1'), (1, False))
        self.assertEqual(get_page_details('100'), (100, False))
        self.assertEqual(get_page_details('1234'), (1234, False))

    def test_invalid(self):
        self.assertRaises(ValueError, get_page_details, 'o')
        self.assertRaises(ValueError, get_page_details, '0')
        self.assertRaises(ValueError, get_page_details, '')
        self.assertRaises(ValueError, get_page_details, '-1')
