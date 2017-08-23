from django import forms

from books.models import Author, Book, Section
from vocab.models import TermCategory


class DynamicSelect(forms.widgets.Select):
    def __init__(self):
        super(DynamicSelect, self).__init__(
            attrs={
                # temporarily disabled cus of Semantic issue #2072
                #'class': 'ui selection dropdown',
                'onchange': 'this.form.submit()',
            },
        )


class SearchFilterForm(forms.Form):
    author = forms.ModelChoiceField(
        Author.objects.none(),
        required=False,
        widget=DynamicSelect()
    )
    book = forms.ModelChoiceField(
        Book.objects.none(),
        required=False,
        widget=DynamicSelect(),
    )
    section = forms.ModelChoiceField(
        Section.objects.none(),
        required=False,
        widget=DynamicSelect(),
    )
    min_rating = forms.ChoiceField(
        choices=(
            (None, '---'),
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
        ),
        required=False,
        widget=DynamicSelect(),
    )
    max_rating = forms.ChoiceField(
        choices=(
            (None, '---'),
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
        ),
        required=False,
        widget=DynamicSelect(),
    )
    category = forms.ModelChoiceField(
        TermCategory.objects.all(),
        required=False
    )
