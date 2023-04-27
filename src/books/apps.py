from __future__ import unicode_literals

from django.apps import AppConfig


class BooksConfig(AppConfig):
    name = 'books'

    def ready(self):
        from books.signal_handlers import delete_related_book_details
