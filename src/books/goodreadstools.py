import os
from datetime import datetime

from goodreads import client

from books import redistools


_client = client.GoodreadsClient(
    os.environ.get('GOODREADS_KEY'),
    os.environ.get('GOODREADS_SECRET'),
)
_client.authenticate(
    access_token=os.environ.get('GOODREADS_ACCESS_TOKEN'),
    access_token_secret=os.environ.get('GOODREADS_ACCESS_SECRET'),
)


def get_author_by_name(name):
    author = _client.find_author(name)
    if author is not None:
        return redistools.save_author(author)


def get_author_by_id(goodreads_id):
    cached_data = redistools.get_author(goodreads_id)
    if cached_data:
        return cached_data

    return redistools.save_author(_client.author(goodreads_id))


def get_books_by_title(title):
    books = []
    for book in _client.search_books(title):
        books.append(redistools.save_book(book))
    
    return books


def get_book_by_id(goodreads_id):
    cached_data = redistools.get_book(goodreads_id)
    if cached_data:
        return cached_data

    return redistools.save_book(_client.book(goodreads_id))


def get_user():
    return _client.user()
 

# todo: the dictionary should be in redistools
def get_read_shelf(page=1):
    reviews = []
    for review in _client.user().reviews(page=page):
        if 'read' not in review.shelves:
            continue

        reviews.append({
            'book': redistools.save_book(review.book),
            'shelves': '/'.join(review.shelves),
            'review': review.body or '',
            'rating': int(review.rating),
            'start_date': review.start_date,
            'end_date': review.end_date,
        })

    return reviews
