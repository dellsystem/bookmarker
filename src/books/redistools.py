import json
import redis

from django.conf import settings


_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0
)


AUTHOR_KEY = 'author:{}'
def get_author(goodreads_id):
    # return none if nothing is stored
    key = AUTHOR_KEY.format(goodreads_id)

    value = _client.get(key)
    if value is not None:
        return json.loads(value)


def save_author2(author_data, titles=None):
    key = AUTHOR_KEY.format(author_data.gid)

    # If author_data is empty, save it anyway.
    if author_data is None:
        value = None
    else:
        # Figure out the titles from the author's books, if any.
        if titles is None:
            titles = ', '.join(
                sorted([book.title for book in author_data.books])
            )

        value = {
            'id': author_data.gid,
            'name': author_data.name,
            'link': author_data.link,
            'titles': titles,
        }

    # If value is None, dumps and loads cancel out
    _client.set(key, json.dumps(value))

    # Return the dictionary being stored
    return value



def save_author(author_data, titles=None):
    key = AUTHOR_KEY.format(author_data['id'])

    # If author_data is empty, save it anyway.
    if author_data is None:
        value = None
    else:
        # Figure out the titles from the author's books, if any.
        if titles is None:
            titles = 'unknown'
            """
            titles = ', '.join(
                sorted([book.title for book in author_data.books])
            )
            """

        value = {
            'id': author_data['id'],
            'name': author_data['name'],
            'link': author_data['link'],
            'titles': titles,
        }

    # If value is None, dumps and loads cancel out
    _client.set(key, json.dumps(value))

    # Return the dictionary being stored 
    return value


BOOK_KEY = 'book:{}'
def get_book(goodreads_id):
    # return none if nothing is stored
    key = BOOK_KEY.format(goodreads_id)

    value = _client.get(key)
    if value is not None:
        return json.loads(value)


def save_book2(book_data):
    key = BOOK_KEY.format(book_data.gid)
    if book_data is None:
        value = None
    else:
        authors = []
        for author_data in book_data.authors:
            # While we have the author data, store that too.
            author = save_author2(author_data, titles=book_data.title)
            authors.append(author)

        value = {
            'id': book_data.gid,
            'title': book_data.title,
            'link': book_data.link,
            'format': book_data.format,
            'year': book_data.publication_date[2],
            'isbn13': book_data.isbn13,
            'publisher': book_data.publisher,
            'num_pages': book_data.num_pages,
            'image_url': book_data.image_url,
            'authors': authors,
        }

    # If value is None, dumps and loads cancel out
    _client.set(key, json.dumps(value))

    # Return the dictionary being stored
    return value



def save_book(book_data):
    key = BOOK_KEY.format(book_data['id']['#text'])
    if book_data is None:
        value = None
    else:
        if 'author' in book_data['authors']:
            authors = [save_author(book_data['authors']['author'], titles=book_data['title'])]
        else:
            print('missing author key:')
            print(book_data['authors'])
            """
            authors = []
            for author_data in book_data['authors']:
                # While we have the author data, store that too.
                author = save_author(author_data, titles=book_data['title'])
                authors.append(author)
            """

        value = {
            'id': book_data['id']['#text'],
            'title': book_data['title'],
            'link': book_data['link'],
            'format': book_data['format'],
            'year': book_data['publication_year'],
            'isbn13': book_data['isbn13'],
            'publisher': book_data['publisher'],
            'num_pages': book_data['num_pages'],
            'image_url': book_data['image_url'],
            'authors': authors,
        }

    # If value is None, dumps and loads cancel out
    print('saving book')
    print(value)
    print(book_data)
    input('waiting')
    _client.set(key, json.dumps(value))

    # Return the dictionary being stored 
    return value


IGNORED_KEY = 'ignored'
REVIEW_KEY = 'reviews:{}'
def ignore_review(goodreads_id):
    _client.sadd(IGNORED_KEY, goodreads_id)
    _client.delete(REVIEW_KEY.format(goodreads_id))


def is_ignored(goodreads_id):
    return _client.sismember(IGNORED_KEY, goodreads_id)


def save_review(goodreads_id, review):
    key = REVIEW_KEY.format(goodreads_id)
    _client.set(key, json.dumps(review))


def count_reviews():
    return len(_client.keys(REVIEW_KEY.format('*')))


def load_review(key):
    value = _client.get(key)
    if value is not None:
        value = json.loads(value)
        # fix bad isbns - TODO: remove
        isbn = value['book']['isbn13']
        if type(isbn) == dict:
            value['book']['isbn13'] = ''
        return value


def get_review(goodreads_id):
    key = REVIEW_KEY.format(goodreads_id)
    return load_review(key)


def get_random_review():
    # Returns one random review.
    keys = _client.keys(REVIEW_KEY.format('*'))
    for key in keys:
        return load_review(key)
