import bs4
import collections
# hacking bs4 support for latest Python
collections.Callable = collections.abc.Callable
from datetime import datetime
import requests
import urllib.parse

from django.conf import settings

from books.models import BookDetails, GoodreadsAuthor, IgnoredBook


USER_ID = '60292716-wendy-liu'
BASE_URL = "https://www.goodreads.com"
BOOK_URL = BASE_URL + '/book/show/'
READ_URL = BASE_URL + "/review/list_rss/{}?shelf=read&sort=date_read&order=d".format(USER_ID)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'


def _parse_num_pages(field):
    """Expect input like '123\n     p'"""
    if field:
        text = field.strip()
        number = text.splitlines()[0].strip()
        if number:
            try:
                return int(number)
            except ValueError:
                # Just return None, it's fine, whatever
                pass

def _parse_id(field):
    """Input format: /book/show/12345.optionaltitle-morestuff"""
    return field.split('/')[-1].split('-')[0].split('.')[0]


def _strip_cdata(text):
    # Some of the fields are like this
    if text and text.startswith('[CDATA[') and text.endswith(']]'):
        return text[7:-2].strip()
    return text


def _parse_rss(content):
    soup = bs4.BeautifulSoup(content, "xml")
    rows = soup.select("rss item")
    books = []
    goodreads_book_ids = set()
    goodreads_author_names = set()
    for row in rows:
        # I HATE GOODREADS
        title = _strip_cdata(row.select_one('title').string)
        goodreads_id = row.select_one('book_id').text.strip()
        goodreads_url = BOOK_URL + goodreads_id
        shelves = _strip_cdata(row.select_one('user_shelves').string)
        review = _strip_cdata(row.select_one('user_review').string)
        year = row.select_one('book_published').text.strip()
        isbn = row.select_one('isbn').text.strip()
        num_pages = _parse_num_pages(row.select_one('num_pages').text)
        image_url = _strip_cdata(row.select_one('book_large_image_url').string)
        rating = int(row.select_one('user_rating').text.strip())
        author_name = row.select_one('author_name').text.strip()

        ignore_link_params = urllib.parse.urlencode({
            'goodreads_id': goodreads_id,
            'description': title,
        })

        book = {
            'title': title,
            'id': goodreads_id,
            'link': goodreads_url,
            'shelves': shelves,
            'review': review,
            'year': year,
            'isbn': isbn,
            'num_pages': num_pages,
            'image_url': image_url,
            'rating': rating,
            'author_name': author_name,
            'ignore_link_params': ignore_link_params,
        }
        goodreads_book_ids.add(goodreads_id)
        goodreads_author_names.add(author_name)
        books.append(book)

    # Figure out which of the books and authors are already in our DB
    details_query = BookDetails.objects.filter(goodreads_id__in=goodreads_book_ids)
    details_dict = {}
    for d in details_query:
        details_dict[d.goodreads_id] = d

    author_query = GoodreadsAuthor.objects.filter(author__name__in=goodreads_author_names)
    author_dict = {}
    for a in author_query:
        author_dict[a.author.name] = a.author

    # Figure out which books need to be ignored
    ignored_book_ids = set(IgnoredBook.objects.values_list('goodreads_id', flat=True))

    # Now go back through the books list to update the status
    # We only need to return books that are either not in the db or that have
    # some sort of mistake to be corrected.
    filtered_books = []
    for book in books:
        if book['id'] in ignored_book_ids:
            continue

        a = author_dict.get(book['author_name'])
        author_id = a.pk if a is not None else ''
        author_slug = a.slug if a is not None else ''
        book['author_id'] = author_id
        book['author_slug'] = author_slug
        if not a:
            book['author_params'] = urllib.parse.urlencode({
                'name': book['author_name'],
            })

        d = details_dict.get(book['id'])
        if d:
            b = d.book
            book['is_processed'] = b.is_processed
            book['slug'] = b.slug

            if book['is_processed']:
                continue
        else:
            # Create a URL to quickly create the book (query params)
            book['book_params'] = urllib.parse.urlencode({
                'title': book['title'],
                'id': book['id'],
                'link': book['link'],
                'shelves': book['shelves'],
                'review': book['review'],
                'year': book['year'],
                'isbn': book['isbn'],
                'rating': book['rating'],
                'num_pages': book['num_pages'],
                'image_url': book['image_url'],
                'author_name': book['author_name'],
                'author_id': author_id,
                'author_slug': author_slug,
            })

        filtered_books.append(book)

    return filtered_books


def get_books(page):
    """This is a horrible and obviously temporary workaround but I guess Goodreads just changed their website to require auth for the review list page. So we fake it by sending some cookies to simulate being logged in. I just downloaded some subset from my current active session which seems to work. I think the earliest one expires Oct 24 2026. Whatever, I'll deal with it then.
    Not checked into source control for obvious reasons. Must be added as an environment variable.
    NEW AS OF JUL 14 2026: The previous URL returns a 202 so I guess I'd better switch to the RSS link.
    """
    cookies = {
        'at-main': settings.GOODREADS_AT_COOKIE,
        'ubid-main': settings.GOODREADS_UBID_COOKIE,
    }
    url = '{}&page={}'.format(READ_URL, page)
    response = requests.get(url, headers={
        'User-Agent': USER_AGENT  # we just need a fake user agent or it 403s
    }, cookies=cookies)
    response.raise_for_status()
    # TODO: collections.abc.Callable
    return _parse_rss(response.content.decode())
