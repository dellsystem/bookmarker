from goodreads import client

from .conf import GOODREADS_KEY, GOODREADS_SECRET


CLIENT = client.GoodreadsClient(GOODREADS_KEY, GOODREADS_SECRET)
