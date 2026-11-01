from django.test import TestCase

from books.models import Author
from books.forms import MultipleSectionsForm


class TestMultipleSectionsForm(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_author_name(self):
        author = Author.objects.create(name='Author 1')
        text = """
        1. Title1  \\a Author 1 1
        2. Title2 \\a Author 2 2
        3. Title3 3
        """
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'group_name': None, 'page_number': 1, 'in_preface': False, 'number': 1, 'title': 'Title1',  'author_name': 'Author 1', 'author_id': author.id},
                {'group_name': None, 'page_number': 2, 'in_preface': False, 'number': 2, 'title': 'Title2',  'author_name': 'Author 2', 'author_id': None},
                {'group_name': None, 'page_number': 3, 'in_preface': False, 'number': 3, 'title': 'Title3',  'author_name': None, 'author_id': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )

    def test_long_group_name(self):
        text = """
The ‘Dark Continent’ of Film Noir: Race, Displacement and Metaphor in Tourneur’s Cat People (1942) and Welles’ The Lady from Shanghai (1948)
1. Title1 1
2. Title2 2
"""
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'group_name': 'The ‘Dark Continent’ of Film Noir: Race, Displacement and Metaphor in Tourneur’s Cat People (1942) …', 'page_number': 1, 'in_preface': False, 'number': 1, 'title': 'Title1',  'author_name': None, 'author_id': None},
                {'group_name': 'The ‘Dark Continent’ of Film Noir: Race, Displacement and Metaphor in Tourneur’s Cat People (1942) …', 'page_number': 2, 'in_preface': False, 'number': 2, 'title': 'Title2',  'author_name': None, 'author_id': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )

    def test_long_section_title(self):
        text = """
        1. The ‘Dark Continent’ of Film Noir: Race, Displacement and Metaphor in Tourneur’s Cat People (1942) and Welles’ The Lady from Shanghai (1948) The ‘Dark Continent’ of Film Noir: Race, Displacement and Metaphor in Tourneur’s Cat People (1942) and Welles’ The Lady from Shanghai (1948) 183
        """
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'title': 'The ‘Dark Continent’ of Film Noir: Race, Displacement and Metaphor in Tourneur’s Cat People (1942) and Welles’ The Lady from Shanghai (1948) The ‘Dark Continent’ of Film Noir: Race, Displacement and Metaphor in Tourneur’s Cat People (1942) and Welles’…', 'page_number': 183, 'in_preface': False, 'number': 1, 'group_name': None,  'author_name': None, 'author_id': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )

    def test_without_section_numbers(self):
        text = """
        Preface x
        PARTONE
        Introduction 1
        One 7
        PART TWO
        Two Two 25
        Three Three Three 35
        
        Conclusion 50
        """
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'title': 'Preface', 'page_number': 10, 'in_preface': True, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': False, 'number': None, 'group_name': 'PARTONE', 'author_name': None, 'author_id': None},
                {'title': 'One', 'page_number': 7, 'in_preface': False, 'number': None, 'group_name': 'PARTONE',  'author_name': None, 'author_id': None},
                {'title': 'Two Two', 'page_number': 25, 'in_preface': False, 'number': None, 'group_name': 'PART TWO',  'author_name': None, 'author_id': None},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': False, 'number': None, 'group_name': 'PART TWO',  'author_name': None, 'author_id': None},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )

    def test_with_section_numbers(self):
        text = """
        Preface x
        Introduction 1
        1. One 7
        2. Two Two 25
        3. Three Three Three 35
        4.1 Blah 45
        Conclusion 50
        """
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'title': 'Preface', 'page_number': 10, 'in_preface': True, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'One', 'page_number': 7, 'in_preface': False, 'number': 1, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Two Two', 'page_number': 25, 'in_preface': False, 'number': 2, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': False, 'number': 3, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': '4.1 Blah', 'page_number': 45, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )

    def test_bad_section_numbers(self):
        text = """
        Preface x
        Introduction 1
        One 7
        1.1 Two Two 25
        Three Three Three 35
        Conclusion 50
        """
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'title': 'Preface', 'page_number': 10, 'in_preface': True, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'One', 'page_number': 7, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': '1.1 Two Two', 'page_number': 25, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': False, 'number': None, 'group_name': None,  'author_name': None, 'author_id': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )
