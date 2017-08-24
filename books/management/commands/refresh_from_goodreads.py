from datetime import datetime

from django.core.management.base import NoArgsCommand

from books.api import CLIENT
from books.models import Book


DATE_FORMAT = '%a %b %d %H:%M:%S %Y'
class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        CLIENT.authenticate()
        user = CLIENT.user('60292716')
        page = 1
        all_reviews = []
        while True:
            reviews = user.reviews(page=page)
            all_reviews.extend(reviews)
            if not reviews:
                break

            page += 1
            print page, len(reviews)

            for review in reviews:
                goodreads_id = review.book['id']['#text']
                try:
                    book = Book.objects.get(goodreads_id=goodreads_id)
                except Book.DoesNotExist:
                    continue

                print "Found book", book.title
                book.rating = int(review.rating)
                if review.started_at:
                    book.start_date = datetime.strptime(
                        review.started_at[:-10] + review.started_at[-4:],
                        DATE_FORMAT
                    ).date()
                if review.read_at:
                    book.end_date = datetime.strptime(
                        review.read_at[:-10] + review.read_at[-4:],
                        DATE_FORMAT
                    ).date()
                print book.rating, book.start_date, book.end_date
                book.save()
