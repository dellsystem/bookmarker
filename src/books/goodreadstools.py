import bs4
from datetime import datetime
import requests
import urllib.parse

from django.conf import settings

from books.models import BookDetails, GoodreadsAuthor, IgnoredBook


RESOLUTION = '_SY475_'
def _parse_image_url(field):
    """We may need to replace the last few chars to get a high-res image URL"""
    if field:
        text = field.strip()
        if text.endswith('_.jpg'):
            segments = text.split('.')
            resolution = segments[-2]
            if resolution.startswith('_S') and resolution.endswith('_'):
                segments[-2] = RESOLUTION
                return '.'.join(segments)

        return text


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

def _parse_date(field):
    if field:
        text = field.strip()
        if ',' in text:
            format_string = '%b %d, %Y'
        else:
            format_string = '%b %Y'
        return datetime.strptime(
            text,
            format_string
        ).date()


USER_ID = '60292716-wendy-liu'
BASE_URL = "https://www.goodreads.com"
READ_URL = BASE_URL + "/review/list/{}?shelf=read&sort=date_read".format(USER_ID)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
def get_books(page):
    """This is a horrible and obviously temporary workaround but I guess Goodreads just changed their website to require auth for the review list page. So we fake it by sending some cookies to simulate being logged in. I just downloaded some subset from my current active session which seems to work. I think the earliest one expires Oct 24 2026. Whatever, I'll deal with it then.
    Not checked into source control for obvious reasons. Must be added as an environment variable.
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
    soup = bs4.BeautifulSoup(response.content.decode(), "html.parser")
    rows = soup.select("table#books tbody tr")

    books = []
    goodreads_book_ids = set()
    goodreads_author_ids = set()
    for row in rows:
        # I HATE GOODREADS
        title_tag = row.select('.field.title .value a')[0]
        goodreads_url = title_tag['href']
        goodreads_id = _parse_id(goodreads_url)
        title = title_tag.text.strip()

        author_tag = row.select('.field.author .value a')[0]
        author_url = author_tag['href']
        author_id = _parse_id(author_url)
        author_name = author_tag.text.strip()
        if author_name:
            # Flip the author name around (last, first to first, last)
            author_name = ' '.join(author_name.split(', ')[::-1])

        # Doing this kind of annoying if/else statement just cus i want to make
        # _parse_date feel better for testing [operating on strings, not bs4
        # objects]
        start_date = row.select('.date_started_value')
        if start_date:
            start_date = _parse_date(start_date[0].text)
        else:
            start_date = None
        end_date = row.select('.date_read_value')
        if end_date:
            end_date = _parse_date(end_date[0].text)
        else:
            end_date = None

        book_format = row.select('.format .value')[0].text.strip()
        isbn = row.select('.isbn13 .value')[0].text.strip()
        num_pages = _parse_num_pages(row.select('.num_pages .value')[0].text)
        image_url = _parse_image_url(row.select('img')[0]['src'])

        # If the publication year is missing or weirdly formatted (sometimes it
        # just is for whatever reason, see if it's present in the
        # date_pub_edition field instead
        year = row.select('.date_pub .value')[0].text.strip()
        if year == 'unknown' or ',' in year:
            pub_date = row.select('.date_pub_edition .value')[0].text.strip()
            year = pub_date.split(',')[-1].strip()

        ignore_link_params = urllib.parse.urlencode({
            'goodreads_id': goodreads_id,
            'description': title,
        })

        book = {
            'id': goodreads_id,
            'url': BASE_URL + goodreads_url,
            'title': title,
            'start_date': start_date,
            'end_date': end_date,
            'format': book_format,
            'isbn': isbn,
            'num_pages': num_pages,
            'image_url': image_url,
            'year': year, # convert this to number? maybe
            # TODO: author, publisher name
            'author_url': BASE_URL + author_url,
            'author_name': author_name,
            'author_id': author_id,
            'ignore_link_params': ignore_link_params,
        }
        goodreads_book_ids.add(goodreads_id)
        goodreads_author_ids.add(author_id)
        books.append(book)

    # Figure out which of the books and authors are already in our DB
    details_query = BookDetails.objects.filter(goodreads_id__in=goodreads_book_ids)
    details_dict = {}
    for d in details_query:
        details_dict[d.goodreads_id] = d

    author_query = GoodreadsAuthor.objects.filter(goodreads_id__in=goodreads_author_ids)
    author_dict = {}
    for a in author_query:
        author_dict[a.goodreads_id] = a.author

    # Figure out which books need to be ignored
    ignored_book_ids = set(IgnoredBook.objects.values_list('goodreads_id', flat=True))

    # Now go back through the books list to update the status
    # We only need to return books that are either not in the db or that have
    # some sort of mistake to be corrected.
    filtered_books = []
    for book in books:
        if book['id'] in ignored_book_ids:
            continue

        a = author_dict.get(book['author_id'])
        if a:
            book['author'] = a
        else:
            book['author_params'] = urllib.parse.urlencode({
                'name': book['author_name'],
                'link': book['author_url'],
            })

        d = details_dict.get(book['id'])
        if d:
            b = d.book
            book['is_processed'] = b.is_processed
            book['slug'] = b.slug
            book['dates_match'] = (
                d.start_date == book['start_date'] and
                d.end_date == book['end_date']
            )
            if d.start_date is None and d.end_date is None:
                dates_comment = 'No BM dates'
            else:
                dates_comment = '{} - {}'.format(
                    d.start_date, d.end_date
                )
            book['dates_comment'] = dates_comment

            if book['is_processed'] and book['dates_match']:
                continue
        else:
            # Create a URL to quickly create the book (query params)
            book['book_params'] = urllib.parse.urlencode({
                'id': book['id'],
                'title': book['title'],
                'link': book['url'],  # todo: url to link. also prepend site
                'isbn': book['isbn'],
                'year': book['year'],
                'format': book['format'],
                'num_pages': book['num_pages'],
                'start_date': book['start_date'],
                'end_date': book['end_date'],
                'image_url': book['image_url'],
                'author_name': book['author_name'],
                'author_url': book['author_url'],
                'author_id': a.pk if a is not None else '',
                'author_slug': a.slug if a is not None else '',
            })

        filtered_books.append(book)

    return filtered_books


AUTHOR_URL = BASE_URL + '/author/show/'
def get_author_id(link):
    """Given a URL, if it's a goodreads author url, return the goodreads ID.
    else, return none"""
    if link.startswith(AUTHOR_URL):
        return link.lstrip(AUTHOR_URL).split('.')[0]
