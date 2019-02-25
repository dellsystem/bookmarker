from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import mark_safe

from .models import Author, Book, Note, TagCategory, Tag, Section


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'goodreads_id']
    prepopulated_fields = {'slug': ('name',), }
    search_fields = ['name']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'get_page_display', 'book']
    list_filter = ['book']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['subject', 'section', 'book', 'get_page_display']
    search_fields = ['subject', 'quote', 'comment']


@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ['slug', 'description', 'colour']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['display_tag', 'description', 'faved']
    list_display_links = None

    def display_tag(self, obj):
        if obj.category:
            return mark_safe(
                '<a class="ui large {c} label" href="{u}">{s1} / {s2}</a>'.format(
                    c=obj.category.colour,
                    u=reverse('admin:books_tag_change', args=[obj.id]),
                    s1=obj.category.slug,
                    s2=obj.slug,
                )
            )
        else:
            return obj.slug
