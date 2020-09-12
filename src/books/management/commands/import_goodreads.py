import csv

from django.core.management.base import BaseCommand

from books import redistools, goodreadstools
from books.models import Book, BookDetails


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
            details = BookDetails.objects.filter(goodreads_id=goodreads_id)
            if not details.exists():
                continue

            d = details.first()
            to_update = {}

            title = row[1]
            isbn = row[6].strip('=').strip('"')
            rating = int(row[7])
            publisher = row[9]
            format = row[10]
            num_pages = int(row[11]) if row[11] else None
            year = int(row[12]) if row[12] else None
            end_date = row[14]
            shelves = row[16]
            review = row[19]

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
