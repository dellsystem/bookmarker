from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe

from .models import GoodreadsAuthor, Author, Book, BookDetails, BookLocation, \
                    Note, TagCategory, Tag, ReadingGoal, Section, IgnoredBook


class GoodreadsAuthorInline(admin.TabularInline):
    model = GoodreadsAuthor


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',), }
    search_fields = ['name']
    inlines = [GoodreadsAuthorInline]


@admin.register(ReadingGoal)
class GoalAdminAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(BookLocation)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_physical']
    search_fields = ['name']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'get_page_display', 'book']
    list_filter = ['book']
    autocomplete_fields = ['related_to']
    search_fields = ['title']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    search_fields = ['title']


@admin.register(BookDetails)
class BookDetailsAdmin(admin.ModelAdmin):
    list_display = ['book']
    search_fields = ['book__title']


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
        return mark_safe(
            '<a class="ui large {c} label" href="{u}">{s}</a>'.format(
                c=obj.get_colour(),
                u=reverse('admin:books_tag_change', args=[obj.id]),
                s=obj,
            )
        )


@admin.register(IgnoredBook)
class IgnoredBookAdmin(admin.ModelAdmin):
    list_display = ['description', 'reason']
