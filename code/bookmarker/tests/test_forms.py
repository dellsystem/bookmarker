from django.test import TestCase

from books.forms import MultipleSectionsForm


class TestMultipleSectionsForm(TestCase):
    def test_without_section_numbers(self):
        text = """
        Preface x
        Introduction 1
        One 7
        Two Two 25
        Three Three Three 35
        Conclusion 50
        """
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'title': 'Preface', 'page_number': 10, 'in_preface': 1, 'number': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': 0, 'number': None},
                {'title': 'One', 'page_number': 7, 'in_preface': 0, 'number': None},
                {'title': 'Two Two', 'page_number': 25, 'in_preface': 0, 'number': None},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': 0, 'number': None},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': 0, 'number': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )

    def test_with_section_numbers(self):
        text = """
        Preface x
        Introduction 1

        1.One 7
        2.Two Two 25
        3.Three Three Three 35
        Conclusion 50
        """
        form = MultipleSectionsForm(data={'sections': text})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            [
                {'title': 'Preface', 'page_number': 10, 'in_preface': 1, 'number': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': 0, 'number': None},
                {'title': 'One', 'page_number': 7, 'in_preface': 0, 'number': 1},
                {'title': 'Two Two', 'page_number': 25, 'in_preface': 0, 'number': 2},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': 0, 'number': 3},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': 0, 'number': None},
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
                {'title': 'Preface', 'page_number': 10, 'in_preface': True, 'number': None},
                {'title': 'Introduction', 'page_number': 1, 'in_preface': False, 'number': None},
                {'title': 'One', 'page_number': 7, 'in_preface': False, 'number': None},
                {'title': '1.1 Two Two', 'page_number': 25, 'in_preface': False, 'number': None},
                {'title': 'Three Three Three', 'page_number': 35, 'in_preface': False, 'number': None},
                {'title': 'Conclusion', 'page_number': 50, 'in_preface': False, 'number': None},
            ],
            form.cleaned_data['sections'],
            "Checking output of clean_sections()"
        )
