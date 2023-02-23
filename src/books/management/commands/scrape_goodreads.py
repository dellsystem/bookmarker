"""Inspired by https://github.com/rixx/goodreads-to-sqlite (just the scrape
function).
I don't know why the params dict isn't working (I just hardcoded the params in
the URL
This is only for updating dates of books that are already in the db
"""
import bs4
from datetime import datetime
import requests

from django.core.management.base import BaseCommand

from books import redistools, goodreadstools
from books.models import Book, BookDetails


USER_ID = '60292716-wendy-liu'
BASE_URL = "https://www.goodreads.com/"
URL = BASE_URL + "review/list/{}?shelf=read&per_page=100&sort=date_updated".format(USER_ID)
class Command(BaseCommand):
    def handle(self, **options):
        """
        params = {
            #"utf8": "✓",
            "per_page": "100",  # Maximum allowed page size
            "sort": "date_updated",
            "page": 0,
        }
        """
        date_counter = 0
        while True:
            #print("Page", params['page'])
            #params["page"] += 1
            #response = requests.get(URL, data=params)
            response = requests.get(URL)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.content.decode(), "html.parser")

            rows = soup.select("table#books tbody tr")
            for row in rows:
                title_tag = row.select('.field.title .value a')[0]
                goodreads_id = title_tag['href'].split('/')[-1].split('-')[0]
                title = title_tag.text.strip()

                details = BookDetails.objects.filter(goodreads_id=goodreads_id)
                if not details.exists():
                    continue
                details = details.first()

                date = row.select(".date_read_value")
                if not date:
                    continue

                date = date[0].text.strip()
                if ',' in date:
                    format_string = '%b %d, %Y'
                else:
                    format_string = '%b %Y'
                read_at = datetime.strptime(
                    date,
                    format_string
                ).date()
                date_counter += 1
                if not details.end_date:
                    print("Updating read date", goodreads_id, title, read_at)
                    details.end_date = read_at
                    details.save()

            if not soup.select("a[rel=next]"):
                break
