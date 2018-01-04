from datetime import datetime

from django.core.management.base import NoArgsCommand

from books.api import CLIENT
from books.models import Book, BookDetails


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
                all_details = BookDetails.objects.filter(goodreads_id=goodreads_id)
                for details in all_details:
                    print "Found details", details.book.title
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
                    print details.rating, details.start_date, details.end_date
                    details.save()
