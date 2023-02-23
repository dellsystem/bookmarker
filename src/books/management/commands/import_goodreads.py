import csv
import re

from django.core.management.base import BaseCommand

from books import redistools, goodreadstools
from books.models import Author, Book, BookDetails


AUTHOR_LINK_PREFIX = 'https://www.goodreads.com/author/show/'
BASE_URL = 'https://www.goodreads.com/book/show/'
WHITESPACE_RE = re.compile('\s+')
class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('filename')

    def handle(self, **options):
        f = options['filename']
        reader = csv.reader(open(f))
        print(next(reader))
        for row in reader:
            goodreads_id = row[0]
            title = row[1]
            author = row[2]
            if '  ' in author:
                author = WHITESPACE_RE.sub(' ', author)
            isbn = row[6].strip('=').strip('"')
            rating = int(row[7])
            publisher = row[9]
            format = row[10]
            num_pages = int(row[11]) if row[11] else None
            year = int(row[12]) if row[12] else None
            end_date = row[14]
            if end_date:
                end_date = end_date.replace('/', '-')
            else:
                end_date = None
            shelves = row[16]
            exclusive_shelf = row[18]
            review = row[19]

            details = BookDetails.objects.filter(goodreads_id=goodreads_id)
            if not details.exists() and exclusive_shelf == 'read':
                print('============= {title} - {author} ({year}) [{id}]'.format(
                    title=title,
                    author=author,
                    year=year,
                    id=goodreads_id
                ))
                print('Done: {}'.format(end_date))
                if shelves:
                    print('Shelves: {}'.format(shelves))

                # Check if the author exists
                authors = Author.objects.filter(name=author)
                if authors.exists():
                    author_object = authors.first()
                    print('Author already exists')
                else:
                    print('NEW AUTHOR')
                    while True:
                        author_link = input('{} Goodreads link: '.format(author)).strip()
                        if author_link.startswith(AUTHOR_LINK_PREFIX):
                            break
                        else:
                            print('BAD AUTHOR LINK - TRY AGAIN!!!')
                    author_id = author_link.removeprefix(AUTHOR_LINK_PREFIX)
                    author_id = author_id.split('.')[0]
                    print('Author ID: {}'.format(author_id))
                    author_object = Author.objects.create_from_goodreads({
                        'name': author,
                        'id': author_id,
                        'link': author_link
                    })

                # TODO: create the book
                image_url = input('Book image URL: ')
                book = Book.objects.create_from_goodreads({
                    'id': goodreads_id,
                    'link': BASE_URL + goodreads_id,
                    'year': year,
                    'isbn13': isbn,
                    'publisher': publisher,
                    'num_pages': num_pages,
                    'image_url': image_url,
                    'title': title,
                    'shelves': shelves,
                    'review': review,
                    'format': format,
                    'end_date': end_date,
                })

                book.details.authors.add(author_object)
                book.details.default_authors.add(author_object)
            else:
                continue

            d = details.first()
            to_update = {}


            if not d.isbn and isbn:
                to_update['isbn'] = isbn
            if not d.rating and rating:
                to_update['rating'] = rating
            if not d.publisher and publisher:
                to_update['publisher'] = publisher
            if not d.format and format:
                to_update['format'] = format
            if not d.num_pages and num_pages:
                to_update['num_pages'] = num_pages
            if not d.year and year:
                to_update['year'] = year
            if not d.end_date and end_date:
                to_update['end_date'] = end_date
            if not d.shelves and shelves:
                to_update['shelves'] = shelves
            if not d.review and review:
                to_update['review'] = review

            if to_update:
                print("Updating: {}, {} =======".format(
                    goodreads_id, title)
                )
                print(to_update)
                details.update(**to_update)
