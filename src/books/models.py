from __future__ import unicode_literals
import collections
from heapq import merge
import operator
import re

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from languages.fields import LanguageField

from activity.models import Action
from .utils import int_to_roman, roman_to_int


class AuthorManager(models.Manager):
    def create_from_goodreads(self, author_data):
        """Only call this if you're sure the goodreads author doesn't already
        exist."""
        # Clean the name (get rid of extraneous whitespace).
        name = ' '.join(author_data['name'].split())
        slug = slugify(name)

        # If the author already exists for this slug, assume it's different,
        # and give this author a different slug.
        existing_author = Author.objects.filter(slug=slug)
        if existing_author.exists():
            i = 2
            while True:
                potential_slug = "{}-{}".format(slug, i)
                if Author.objects.filter(slug=potential_slug).exists():
                    i += 1
                else:
                    slug = potential_slug
                    name = "{} {}".format(name, i)
                    break

        # Create the author and the goodreads author.
        author = Author.objects.create(
            name=name,
            link=author_data['link'],
            slug=slug,
        )
        author.goodreadsauthor_set.create(
            goodreads_id=author_data['id'],
            goodreads_link=author_data['link'],
        )
        Action.objects.create(
            category='author',
            primary_id=author.pk,
            details=name,
            verb='added',
        )
        return author


class Author(models.Model):
    name = models.CharField(max_length=100)
    link = models.URLField(help_text='Only needed if no goodreads author')
    slug = models.SlugField(unique=True)
    objects = AuthorManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('view_author', args=[self.slug])


class GoodreadsAuthor(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    goodreads_id = models.CharField(max_length=20, unique=True)
    goodreads_link = models.URLField()


GR_IMAGE_URL_RE = re.compile(r'_SX98_.jpg$')
class BookManager(models.Manager):
    def create_from_goodreads(self, book_data):
        details = BookDetails.objects.create(
            goodreads_id=book_data['id'],
            link=book_data['link'],
            year=int(book_data['year']) if book_data['year'] else None,
            isbn=book_data['isbn13'],
            publisher=book_data['publisher'],
            num_pages=int(book_data['num_pages']) if book_data['num_pages'] else None,
        )

        # Replace the SX98_.jpg at the end with SX475_.jpg
        image_url = book_data['image_url']
        if image_url:
            image_url = GR_IMAGE_URL_RE.sub('_SY475_.jpg', image_url)

        # If there's a :, strip out everything after it for the slug.
        title = book_data['title']
        slug = slugify(title.split(':')[0])
        # Make sure the slug is 50 characters or less
        if len(slug) > 50:
            # First try cutting it to the part before the last -
            # as long as it's not obscenely short
            slug = slug[:50]
            last_dash = slug.rfind('-')
            if last_dash > 10:
                slug = slug[:last_dash]

        # If the book already exists for this slug, give this book a number
        # after the slug.
        existing_book = Book.objects.filter(slug=slug)
        if existing_book.exists():
            i = 2
            while True:
                potential_slug = "{}-{}".format(slug, i)
                if Book.objects.filter(slug=potential_slug).exists():
                    i += 1
                else:
                    slug = potential_slug
                    break

        book = Book.objects.create(
            details=details,
            title=title,
            image_url=image_url,
            slug=slug,
        )

        # Create the relevant action, too.
        Action.objects.create(
            category='book',
            primary_id=book.pk,
            details=title,
            verb='added',
        )

        return book

class RatingField(models.IntegerField):
    def __init__(self, min_value=0, max_value=5, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)


class BookDetails(models.Model):
    """Mostly from Goodreads, though the book doesn't have to be on GR."""
    goodreads_id = models.CharField(max_length=20, blank=True, null=True,
                                    db_index=True)
    link = models.URLField()
    has_pages = models.BooleanField(default=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    issue_number = models.PositiveSmallIntegerField(blank=True, null=True,
        help_text='Only for periodicals (like NLR, Jacobin)'
    )
    publisher = models.CharField(max_length=50, blank=True, null=True)
    format = models.CharField(max_length=25, blank=True, null=True)
    num_pages = models.PositiveSmallIntegerField(blank=True, null=True)
    verified = models.BooleanField(default=False)  # the ISBN and related details
    review = models.TextField(blank=True)
    shelves = models.TextField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    rating = RatingField(default=0, blank=True)
    is_edited = models.BooleanField(
        default=False,
        help_text='If the authors are actually editors'
    )
    # 'authors' is taken directly from GoodReads. Currently used for display
    # purposes only (not when inferring the author for a Section, e.g.).
    # Not currently editable via the web interface.
    authors = models.ManyToManyField(Author, blank=True, related_name='books')
    # The default authors set on a Section/Term/Note if they aren't specified.
    # If empty (e.g., if it's an edited collection), then it's assumed that
    # most sections are by different authors.
    default_authors = models.ManyToManyField(Author,
                                             blank=True,
                                             related_name='default_books')

    class Meta:
        verbose_name_plural = 'Book details'
    
    def __str__(self):
        return self.link


class Book(models.Model):
    """If details are None, then it's a publication, not a book."""
    objects = BookManager()
    details = models.OneToOneField(BookDetails, on_delete=models.CASCADE,
                                   blank=True, null=True)
    title = models.CharField(max_length=255)
    language = LanguageField(default='en')
    image_url = models.URLField()
    is_processed = models.BooleanField(default=False, db_index=True)  # terms, notes, sections
    completed_sections = models.BooleanField(default=False)  # KEEP
    completed_read = models.BooleanField(default=True)
    summary = models.TextField(blank=True)
    comments = models.TextField(blank=True)  # temporary private notes
    source_url = models.URLField(blank=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

    def is_publication(self):
        return self.details is None

    def get_citation_data(self):
        details = self.details
        if details is None:
            is_edited = False
            issue_number = None
            year = None
            publisher = ''
            authors = ''
            num_authors = 0
            title = self.title
        else:
            if details.issue_number:
                # It's a periodical. Set the title to the first author's name.
                if details.default_authors.exists():
                    title = details.default_authors.first().name
                else:
                    title = ''
                authors = ''
                num_authors = 0
            else:
                title = self.title
                author_names = []
                for author in details.default_authors.all():
                    author_name = author.name.split(' ')
                    last_name = ' '.join(author_name[1:])
                    first_initial = author_name[0][0]
                    author_names.append(
                        '{last}, {first}.'.format(last=last_name, first=first_initial)
                    )

                # Join the names with commas and an "and" at the end.
                authors = '?'
                num_authors = len(author_names)
                if num_authors == 1:
                    authors = author_names[0]
                elif num_authors == 2:
                    authors = author_names[0] + ' and ' + author_names[1]
                elif num_authors == 3:
                    authors = (
                        author_names[0] + ', ' + author_names[1] + ' and ' + author_names[2]
                    )
                elif num_authors > 3:
                    authors = author_names[0] + ' et al'
            is_edited = details.is_edited
            issue_number = details.issue_number
            year = details.year
            publisher = details.publisher

        return {
            'is_edited': is_edited,
            'issue_number': issue_number,
            'num_authors': num_authors,
            'authors': authors,
            'year': year,
            'title': title,
            'publisher': publisher,
        }

    def get_citation(self):
        """Streeck, W. (2016). _How will capitalism end? Essays on a failing
        system._ New York: Verso Books."""

        citation_data = self.get_citation_data()
        if citation_data:
            return '{authors} ({year}). _{title}_. {publisher}.'.format(
                **citation_data
            )

    def get_absolute_url(self):
        return reverse('view_book', args=[self.slug])

    def has_pages(self):
        return self.details.has_pages if self.details else False


class PageNumberField(models.PositiveSmallIntegerField):
    def validate(self, value, model_instance):
        if not value.isdigit() and not roman_to_int(value):
            raise forms.ValidationError("Invalid page")

    def to_python(self, value):
        return value

    def formfield(self, **kwargs):
        # Get rid of the min/max value validatosr (Postgres only)
        self.validators = []
        return forms.CharField(**kwargs)


class PageArtefact(models.Model):
    """Inherited by Note, TermOccurrence, and Section."""
    in_preface = models.BooleanField()
    page_number = PageNumberField(default=1)

    class Meta:
        abstract = True

    def get_author_data(self):
        """Returns the mode and authors list (needed for
        populating ArtefactAuthorForm)"""
        authors = []

        if self.authors.count():
            if self.has_default_authors():
                mode = 'default'
            else:
                mode = 'custom'
                authors = self.authors.all()
        else:
            mode = 'none'

        return {
            'mode': mode,
            'authors': authors,
        }

    @property
    def int_page_number(self):
        if self.in_preface:
            return -self.page_number
        else:
            return self.page_number

    def get_page_display(self):
        if self.in_preface:
            return int_to_roman(self.page_number)
        else:
            return self.page_number


class Section(PageArtefact):
    # TODO: unique together for book & number
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
        related_name='sections')
    number = models.PositiveSmallIntegerField(blank=True, null=True,
        help_text='Chapter number (if relevant')
    authors = models.ManyToManyField(Author, related_name='sections', blank=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    rating = RatingField(default=0, blank=True)
    source_url = models.URLField(blank=True)
    related_to = models.ForeignKey('self', on_delete=models.CASCADE,
        blank=True, null=True)
    slug = models.SlugField(blank=True)  # only for link-worthy sections
    skipped = models.BooleanField(default=False, help_text='Not yet read')
    date = models.DateField(blank=True, null=True)  # only publications

    class Meta:
        ordering = ['-in_preface', 'page_number']

    def __str__(self):
        return "{book} - {title}".format(
            title=self.title,
            book=self.book.title
        )

    def is_article(self):
        return self.book.is_publication()

    def get_absolute_url(self):
        return reverse('view_section', args=[str(self.id)])

    def get_artefacts(self):
        """Returns a generator mixing notes and termoccurrences, ordered by
        page (see the int_page_number property on PageArtefact)."""
        return merge(
            self.notes.all().prefetch_related(
                'tags', 'authors', 'section__authors'
            ),
            self.terms.all().prefetch_related(
                'category', 'authors', 'term', 'section__authors',
            ),
            key=lambda x: x.int_page_number
        )

    def has_default_authors(self):
        details = self.book.details
        if details:
            return (
                set(a.pk for a in self.authors.all()) ==
                set(a.pk for a in details.default_authors.all())
            )
        else:
            return False

    def get_citation(self):
        """Gandy, O. H. (2009). Rational discrimination. In _Coming to terms
        with chance: Engaging rational discrimination and cumulative
        disadvantage_. Farnham, VT: Ashgate, pp. 55-76."""
        d = self.book.get_citation_data()
        if not d:
            return

        author_names = []
        for author in self.authors.all():
            author_name = author.name.split(' ')
            last_name = ' '.join(author_name[1:])
            first_initial = author_name[0][0]
            author_names.append(
                '{last}, {first}.'.format(last=last_name, first=first_initial)
            )

        # Join the names with commas and an "and" at the end.
        authors = '?'
        if len(author_names) == 1:
            authors = author_names[0]
        elif len(author_names) == 2:
            authors = author_names[0] + ' and ' + author_names[1]
        elif len(author_names) == 3:
            authors = (
                author_names[0] + ', ' + author_names[1] + ' and ' + author_names[2]
            )
        elif len(author_names) > 3:
            authors = author_names[0] + ' et al'

        d['section_authors'] = authors
        d['section_title'] = self.title
        if d['issue_number']:
            d['in'] = ''
            d['publication'] = d['issue_number']
            d['book_authors'] = ''
            d['book_title'] = d['title'] + ','
        else:
            if self.book.details:
                d['in'] = 'In '
            else:
                d['in'] = ''
            d['publication'] = d['publisher']
            d['book_authors'] = d['authors']
            if d['is_edited']:
                d['book_authors'] += ' (ed{})'.format('s' if d['num_authors'] > 1 else '')
            d['book_title'] = d['title'] + '.'

        if self.book.details:
            d['ending'] = ', pp. {start}-{end}'.format(
                start=self.page_number,
                end=self.get_end_page()
            )
        else:
            d['ending'] = self.source_url

        if self.date:
            d['year'] = self.date.strftime('%Y, %B %d')

        return (
            '{section_authors} ({year}). {section_title}. '
            '{in}{book_authors} _{book_title}_ {publication}{ending}'
        ).format(**d)

    def get_end_page(self):
        next_section = self.book.sections.filter(page_number__gt=self.page_number).order_by('page_number').first()
        if next_section:
            return next_section.page_number - 1
        else:
            if self.book.details and self.book.details.num_pages:
                return self.book.details.num_pages - 1

    def get_next(self):
        """Probably inefficient but the alternative is fairly complex so"""
        found_next = False
        for section in self.book.sections.all():
            if found_next:
                return section

            if section.pk == self.pk:
                found_next = True

    def get_previous(self):
        previous = None
        for section in self.book.sections.all():
            if section.pk == self.pk:
                return previous

            previous = section


class SectionArtefact(PageArtefact):
    """TermOccurrence and Note inherit from this. Section inherits from
    PageArtefact. Defines a determine_section() method that determines the
    correct section (if any) from the page number. Assumes that book is a
    defined field."""

    class Meta:
        abstract = True

    def determine_section(self):
        in_preface = self.in_preface
        sections = self.book.sections.filter(
            in_preface=in_preface,
            page_number__lte=self.page_number,
        )
        return sections.last()

    def has_default_authors(self):
        if self.section:
            return (
                set(a.pk for a in self.authors.all()) ==
                set(a.pk for a in self.section.authors.all())
            )
        else:
            details = self.book.details
            if details:
                return (
                    set(a.pk for a in details.authors.all()) ==
                    set(a.pk for a in details.default_authors.all())
                )
            else:
                return True

    def set_default_authors(self):
        if self.section:
            default_authors = self.section.authors.all()
        else:
            default_authors = self.book.details.default_authors.all()

        self.authors.add(*default_authors)


class TagCategory(models.Model):
    colour = models.CharField(blank=True, max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Tag categories'

    def __str__(self):
        return self.slug


class Tag(models.Model):
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    faved = models.BooleanField(
        default=False,
        help_text='Whether it shows up in the "View faves" page'
    )
    category = models.ForeignKey(TagCategory, on_delete=models.CASCADE,
        blank=True, null=True)

    class Meta:
        ordering = ['category__slug', 'slug']

    def __str__(self):
        if self.category:
            return '{}/{}'.format(self.category.slug, self.slug)
        else:
            return self.slug

    def get_absolute_url(self):
        return reverse('view_tag', args=[self.slug])

    def get_colour(self):
        if self.category:
            return self.category.colour
        else:
            return ''

    def get_authors(self, limit=10):
        author_ids = self.notes.values_list('authors__id', flat=True)
        counter = collections.Counter(author_ids)

        # Return the authors in order of note count (descending), with a limit
        authors = []
        for author_id, count in counter.most_common(limit):
            if author_id is not None:
                authors.append(Author.objects.get(pk=author_id))
        return authors

    def get_bibliography(self):
        book_ids = set()
        section_ids = set()
        for note in self.notes.all().prefetch_related('section', 'book'):
            if note.section_id:
                section_ids.add(note.section_id)
            else:
                book_ids.add(note.book_id)

        # Only include the section if the author is different from the book's
        sections = Section.objects.filter(pk__in=section_ids).prefetch_related(
            'authors'
        )
        books = Book.objects.filter(pk__in=book_ids).prefetch_related(
            'details__default_authors'
        )
        entries = set()
        for book in books:
            entries.add(book)

        for section in sections:
            if section.has_default_authors():
                entries.add(section.book)
            else:
                entries.add(section)

        bibliography = []
        for entry in entries:
            citation = entry.get_citation()
            if citation:
                bibliography.append((citation, entry.get_absolute_url()))

        return sorted(bibliography, key=operator.itemgetter(0))


class Note(SectionArtefact):
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
        related_name='notes')
    added = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=100)
    quote = models.TextField()
    comment = models.TextField(blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE,
        blank=True, null=True, related_name='notes')
    # Should only be empty if the original author isn't in our database.
    # Will usually inherit from the Section, if present, or the book.
    authors = models.ManyToManyField(Author, blank=True, related_name='notes')
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes')

    class Meta:
        ordering = ['-in_preface', 'page_number']

    @property
    def display_template(self):
        return 'note_display.html'

    def get_absolute_url(self):
        return reverse('view_note', args=[str(self.id)])

    def get_citation(self):
        author_names = []
        for author in self.authors.all():
            author_name = author.name.split(' ')
            author_names.append(author_name[-1])  # last name only

        # Join the names with commas and an "and" at the end.
        authors = '?'
        num_authors = len(author_names)
        if num_authors == 1:
            authors = author_names[0]
        elif num_authors == 2:
            authors = author_names[0] + ' and ' + author_names[1]
        elif num_authors == 3:
            authors = (
                author_names[0] + ', ' + author_names[1] + ' and ' + author_names[2]
            )
        elif num_authors > 3:
            authors = author_names[0] + ' et al'

        if self.book.details:
            year = self.book.details.year
        else:
            if self.section.date:
                year = self.section.date.year
            else:
                year = '????'
        return '({authors}, {year}, p.{page})'.format(
            authors=authors,
            year=year,
            page=self.page_number
        )

    def __str__(self):
        return "{subject} - {book}".format(
            subject=self.subject,
            book=self.book.title
        )
