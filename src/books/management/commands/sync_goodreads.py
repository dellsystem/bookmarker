import time

from django.core.management.base import BaseCommand

from books import redistools, goodreadstools
from books.models import Book, BookDetails


def update_details(details, data):
    updated_fields = set()
    # Doing it manually instead of using an update() just in case the data is somehow missing in goodreads
    if data['rating'] and not details.rating:
        details.rating = data['rating']
        updated_fields.add('rating')

    if data['review'] and not details.review:
        details.review = data['review']
        updated_fields.add('review')

    if data['start_date'] and not details.start_date:
        details.start_date = data['start_date']
        updated_fields.add('start_date')

    if data['end_date'] and not details.end_date:
        details.end_date = data['end_date']
        updated_fields.add('end_date')

    if data['shelves'] and not details.shelves:
        details.shelves = data['shelves']
        updated_fields.add('shelves')

    if updated_fields:
        print("Updating details for {}".format(details.book.title))
        for field in updated_fields:
            print("Changed {} to {}".format(
                field, data[field]
            ))
        details.save()


class Command(BaseCommand):
    def handle(self, **options):
        page = 1
        while True:
            reviews = goodreadstools.get_read_shelf(page=page)

            if not reviews:
                break

            page += 1

            for review in reviews:
                goodreads_id = review['book']['id']
                details = BookDetails.objects.filter(goodreads_id=goodreads_id)
                if details.exists():
                    for instance in details.all():
                        update_details(instance, review)
                elif not redistools.is_ignored(goodreads_id):
                    print("Saving", goodreads_id)
                    redistools.save_review(goodreads_id, review)
            print("Done page {}".format(page))
