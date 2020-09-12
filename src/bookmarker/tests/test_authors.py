from django.test import TestCase

from books.models import Author, GoodreadsAuthor


class TestCreateFromGoodreads(TestCase):
    def setUp(self):
        Author.objects.create(
            name='John Smith',
            link='http://johnsmith.com',
            slug='john-smith',
        )

    def test_new_author(self):
        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(GoodreadsAuthor.objects.count(), 0)
        author = Author.objects.create_from_goodreads({
            'id': '123',
            'name': 'Adam Smith',
            'link': 'link',
        })
        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(GoodreadsAuthor.objects.count(), 1)

        self.assertEqual(author.name, 'Adam Smith')
        self.assertEqual(author.slug, 'adam-smith')
        self.assertEqual(author.link, 'link')

        gr_author = author.goodreadsauthor_set.first()
        self.assertEqual(gr_author.goodreads_id, '123')
        self.assertEqual(gr_author.goodreads_link, 'link')
        self.assertEqual(gr_author.author, author)

    def test_messy_author(self):
        """e.g., api results for gr author 7020416"""
        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(GoodreadsAuthor.objects.count(), 0)
        author = Author.objects.create_from_goodreads({
            'id': '7020416',
            'name': 'Tony   McMahon',
            'link': 'link',
        })
        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(GoodreadsAuthor.objects.count(), 1)

        self.assertEqual(author.name, 'Tony McMahon')
        self.assertEqual(author.slug, 'tony-mcmahon')
        self.assertEqual(author.link, 'link')

        gr_author = author.goodreadsauthor_set.first()
        self.assertEqual(gr_author.goodreads_id, '7020416')
        self.assertEqual(gr_author.goodreads_link, 'link')
        self.assertEqual(gr_author.author, author)

    def test_same_slug(self):
        """Add more authors with the same slug."""
        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(GoodreadsAuthor.objects.count(), 0)
        author = Author.objects.create_from_goodreads({
            'id': '999',
            'name': 'John Smith',
            'link': 'link2',
        })
        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(GoodreadsAuthor.objects.count(), 1)

        self.assertEqual(author.name, 'John Smith 2')
        self.assertEqual(author.slug, 'john-smith-2')
        self.assertEqual(author.link, 'link2')

        gr_author = author.goodreadsauthor_set.first()
        self.assertEqual(gr_author.goodreads_id, '999')
        self.assertEqual(gr_author.goodreads_link, 'link2')
        self.assertEqual(gr_author.author, author)

        # Now create a new author.
        other_author = Author.objects.create_from_goodreads({
            'id': '100',
            'name': 'John Smith',
            'link': 'link3',
        })
        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(GoodreadsAuthor.objects.count(), 2)

        self.assertEqual(other_author.name, 'John Smith 3')
        self.assertEqual(other_author.slug, 'john-smith-3')
        self.assertEqual(other_author.link, 'link3')

        other_gr_author = other_author.goodreadsauthor_set.first()
        self.assertEqual(other_gr_author.goodreads_id, '100')
        self.assertEqual(other_gr_author.goodreads_link, 'link3')
        self.assertEqual(other_gr_author.author, other_author)

    def tearDown(self):
        Author.objects.all().delete()
        GoodreadsAuthor.objects.all().delete()
