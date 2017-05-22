from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from books.models import Author
from .models import TermCategory, Term, TermOccurrence


class TermOccurrenceInline(admin.StackedInline):
    model = TermOccurrence
    extra = 0


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('text', 'definition', 'language')
    inlines = [TermOccurrenceInline]
    search_fields = ['text', 'definition']


@admin.register(TermOccurrence)
class TermOccurrenceAdmin(admin.ModelAdmin):
    list_filter = ('book', 'authors')
    list_display = ('term', 'get_page_display', 'book', 'is_new',
                    'is_defined', '_get_category')

    def _get_category(self, obj):
        alpha = '%.2f' % (obj.category.confidence / 100.)
        if obj.category.confidence > 60:
            colour = 'white'
        else:
            colour = 'black'
        return format_html(
            u'<div style="background: rgba(0, 84, 133, {}); color: {}">'
            u'{}</div>',
            alpha,
            colour,
            obj.category.name
        )


@admin.register(TermCategory)
class TermCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'confidence')
    order_by = ['number']
