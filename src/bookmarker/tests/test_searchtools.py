import datetime

from django.test import TestCase

from books import searchtools
from bookmarker.forms import SearchFilterForm
from books.models import Book


class TestGetSearchResults(TestCase):
    def test_bad_query(self):
        self.assertRaises(searchtools.BadQueryException, searchtools.get_search_results, query='1')

    def test_basic_query(self):
        Book.objects.create(title='abc', slug='abc')
        Book.objects.create(title='def', slug='def')
        results, filters_dict = searchtools.get_search_results(query='abc')
        self.assertEqual(results['books'].count(), 1, '1 book')
        self.assertEqual(results['books'].first().title, 'abc', 'book title should be abc')
        self.assertEqual(results['notes'].count(), 0, '0 notes')
        self.assertEqual(results['sections'].count(), 0, '0 sections')
        self.assertEqual(results['terms'].count(), 0, '0 terms')

    def test_query_multiple_results(self):
        book1 = Book.objects.create(title='abc', slug='abc')
        book2 = Book.objects.create(title='abcdef', slug='abcdef')
        results, filters_dict = searchtools.get_search_results(query='abc')
        self.assertEqual(results['books'].count(), 2, '2 books')
        self.assertEqual(results['notes'].count(), 0, '0 notes')
        self.assertEqual(results['sections'].count(), 0, '0 sections')
        self.assertEqual(results['terms'].count(), 0, '0 terms')

    def test_filter_query(self):
        book1 = Book.objects.create(title='abc', slug='abc')
        book2 = Book.objects.create(title='def', slug='def')
        section1 = book1.sections.create(title='section 1')
        section2 = book2.sections.create(title='section 2')
        filter_form = SearchFilterForm({'book': book1.pk})
        results, filters_dict = searchtools.get_search_results(query='section', mode='sections', filter_form=filter_form)
        self.assertEqual(filters_dict, {'book': book1.pk}, 'filters_dict should include the book')
        self.assertEqual(results['books'].count(), 0, '0 books')
        self.assertEqual(results['notes'].count(), 0, '0 notes')
        self.assertEqual(results['sections'].count(), 1, '1 section')
        self.assertEqual(results['sections'].first().title, 'section 1', 'section title should be section 1')
        self.assertEqual(results['terms'].count(), 0, '0 terms')

    def test_word_boundaries(self):
        Book.objects.create(title='abc', slug='abc')
        Book.objects.create(title='abcd', slug='def')
        results, filters_dict = searchtools.get_search_results(query='"abc"')
        self.assertEqual(results['books'].count(), 1, '1 book')
        self.assertEqual(results['books'].first().title, 'abc', 'book title should be abc')
        self.assertEqual(results['notes'].count(), 0, '0 notes')
        self.assertEqual(results['sections'].count(), 0, '0 sections')
        self.assertEqual(results['terms'].count(), 0, '0 terms')

class TestSearchWithinBook(TestCase):
    pass
