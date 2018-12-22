from django.contrib import admin

from .models import Author, Book, Note, Tag, Section


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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['slug', 'description', 'colour', 'faved']
