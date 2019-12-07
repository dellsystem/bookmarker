import time
from datetime import datetime

from django.core.management.base import BaseCommand

from books.api import USER
from books.models import Book, BookDetails


DATE_FORMAT = '%a %b %d %H:%M:%S %Y'
class Command(BaseCommand):
    def handle(self, **options):
        page = 1
        while True:
            reviews = USER.reviews(page=page)

            if not reviews:
                break

            page += 1

            for review in reviews:
                goodreads_id = review.book['id']['#text']
                all_details = BookDetails.objects.filter(goodreads_id=goodreads_id)
                for details in all_details:
                    print("Found details: " + details.book.title)
                    details.rating = int(review.rating)
                    if review.started_at:
                        details.start_date = datetime.strptime(
                            review.started_at[:-10] + review.started_at[-4:],
                            DATE_FORMAT
                        ).date()
                    if review.read_at:
                        details.end_date = datetime.strptime(
                            review.read_at[:-10] + review.read_at[-4:],
                            DATE_FORMAT
                        ).date()
                    details.shelves = '/'.join(review.shelves)
                    details.review = review.body or ''
                    d = {
                        'rating': details.rating,
                        'start_date': details.start_date,
                        'end_date': details.end_date,
                        'shelves': details.shelves,
                        'review': details.review,
                    }
                    print(d)
                    print("============")
                    details.save()
