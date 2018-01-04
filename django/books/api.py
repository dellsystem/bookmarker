import os

from goodreads import client


CLIENT = client.GoodreadsClient(
    os.environ.get('GOODREADS_KEY'),
    os.environ.get('GOODREADS_SECRET')
)
