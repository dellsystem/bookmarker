from django import forms

from books.models import Note, Section


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        exclude = ['book']
        widgets = {
            'subject': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        exclude = ['book']
        widgets = {
            'title': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }
