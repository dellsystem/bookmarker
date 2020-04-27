import os

from goodreads import client


CLIENT = client.GoodreadsClient(
    os.environ.get('GOODREADS_KEY'),
    os.environ.get('GOODREADS_SECRET'),
)
CLIENT.authenticate(
    access_token=os.environ.get('GOODREADS_ACCESS_TOKEN'),
    access_token_secret=os.environ.get('GOODREADS_ACCESS_SECRET'),
)
USER = CLIENT.user()
