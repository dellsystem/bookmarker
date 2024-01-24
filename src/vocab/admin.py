from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from books.models import Author
from .models import TermCategory, Term, TermOccurrence


def flag_terms(modeladmin, request, queryset):
    queryset.update(flagged=True)
    modeladmin.message_user(
        request,
        'Flagged {n} terms'.format(n=queryset.count()),
        messages.SUCCESS
    )


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('text', 'definition', 'language', 'flagged')
    search_fields = ['text', 'definition']
    actions = [flag_terms]


@admin.register(TermOccurrence)
class TermOccurrenceAdmin(admin.ModelAdmin):
    list_filter = ('book', 'authors')
    list_display = ('term', 'get_page_display', 'book', 'is_new',
                    'is_defined', '_get_category')
    # we need to hide the section from the admin page otherwise it 502's
    exclude = ('section',)

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
