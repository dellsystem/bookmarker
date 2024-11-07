from django.test import TestCase

from books.forms import MultipleSectionsForm


class TestMultipleSectionsForm(TestCase):
    def setUp(self):
        self.maxDiff = None

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
                {'title': 'Preface', 'page_number': 10, 'in_preface': True, 'number': None, 'group_name': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': False, 'number': None, 'group_name': 'PARTONE'},
                {'title': 'One', 'page_number': 7, 'in_preface': False, 'number': None, 'group_name': 'PARTONE'},
                {'title': 'Two Two', 'page_number': 25, 'in_preface': False, 'number': None, 'group_name': 'PART TWO'},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': False, 'number': None, 'group_name': 'PART TWO'},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': False, 'number': None, 'group_name': None},
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
                {'title': 'Preface', 'page_number': 10, 'in_preface': True, 'number': None, 'group_name': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': False, 'number': None, 'group_name': None},
                {'title': 'One', 'page_number': 7, 'in_preface': False, 'number': 1, 'group_name': None},
                {'title': 'Two Two', 'page_number': 25, 'in_preface': False, 'number': 2, 'group_name': None},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': False, 'number': 3, 'group_name': None},
                {'title': '4.1 Blah', 'page_number': 45, 'in_preface': False, 'number': None, 'group_name': None},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': False, 'number': None, 'group_name': None},
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
                {'title': 'Preface', 'page_number': 10, 'in_preface': True, 'number': None, 'group_name': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': False, 'number': None, 'group_name': None},
                {'title': 'One', 'page_number': 7, 'in_preface': False, 'number': None, 'group_name': None},
                {'title': '1.1 Two Two', 'page_number': 25, 'in_preface': False, 'number': None, 'group_name': None},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': False, 'number': None, 'group_name': None},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': False, 'number': None, 'group_name': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )
