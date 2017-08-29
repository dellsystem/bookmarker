from django.contrib import admin

from .models import Author, Book, Note, NoteTag, Section


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'goodreads_id']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'get_page_display', 'book']
    list_filter = ['book']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['subject', 'section', 'book', 'get_page_display']
    search_fields = ['subject', 'quote', 'comment']


@admin.register(NoteTag)
class NoteTagAdmin(admin.ModelAdmin):
    list_display = ['slug', 'description', 'colour']
