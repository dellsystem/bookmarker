from django.contrib import admin

from .models import Author, Book, Note, Section


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'goodreads_id']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'first_page', 'book']
    list_filter = ['book']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'goodreads_id']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['subject', 'author', 'section', 'book', 'page']
