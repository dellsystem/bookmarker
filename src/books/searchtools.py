import re

from django.db.models import Q, Count

from books import highlighter
from books.models import Book, Author, Note, Tag, Section
from vocab.models import TermOccurrence


MODES = ('notes', 'terms', 'sections', 'books')
ORDERING = {
    'notes': 'subject',
    'terms': 'term',
    'sections': 'title',
    'books': 'title',
}
# If we're sorting by a custom field, and we're in the right mode.
SORTS = {
    'notes': ('added', 'subject', 'book', 'section'),
    'terms': ('added', 'term', 'book'),
    'sections': ('title', 'book'),
    'books': ('title', 'id'),
}

MODE_FILTERS = {
    'books': ('author', 'min_rating', 'max_rating'),
    'notes': ('author', 'book' ,'section'),
    'terms': ('author', 'book', 'section', 'category'),
    'sections': ('author', 'book', 'min_rating', 'max_rating'),
}

# To simplify the process of matching names to fields. Annoyingly, some fields
# on the Book model are different so we have to hardcode them below.
FILTER_FIELDS = {
    'author': 'authors',
    'book': 'book',
    'section': 'section',
    'category': 'category',
    'min_rating': 'rating__gte',
    'max_rating': 'rating__lte',
}
BOOK_FILTER_FIELDS = {
    'author': 'details__default_authors',
    'min_rating': 'details__rating__gte',
    'max_rating': 'details__rating__lte',
}

class BadQueryException(Exception):
    pass


def search_within_book(query, book_id):
    """
    Used by bookmarker.views.search_within_book_json
    """
    if not query or len(query) < 3:
        raise BadQueryException

    try:
        book = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        raise BadQueryException

    # todo: method on objectmanager to search by keyword
    notes = book.notes.filter(
        Q(subject__icontains=term) |
        Q(quote__icontains=term) |
        Q(comment__icontains=term)
    )
    terms = book.terms.filter(
        Q(term__text__icontains=term) |
        Q(term__definition__icontains=term) |
        Q(quote__icontains=term) |
        Q(quote__icontains=term)
    )
    sections = book.sections.filter(
        Q(title__icontains=term) |
        Q(authors__name__icontains=term) |
        Q(subtitle__icontains=term) |
        Q(summary__icontains=term)
    )

    results = {'notes': [], 'terms': [], 'sections': []}
    for note in notes:
        results['notes'].append({
            'title': highlighter.highlight(note.subject, query),
            'description': highlighter.highlight(note.quote, query, 200),
            'price': note.get_page_display(),
            'url': note.get_absolute_url(),
        })

    for term in terms:
        results['terms'].append({
            'title': highlighter.highlight(term.term.text, query),
            'description': highlighter.highlight(term.quote, query, 200),
            'price': term.get_page_display(),
            'url': term.get_absolute_url(),
        })

    for section in sections:
        authors = ', '.join(a.name for a in section.authors.all())
        results['sections'].append({
            'title': highlighter.highlight(section.title, query),
            'description': highlighter.highlight(authors, query),
            'price': section.get_page_display(),
            'url': section.get_absolute_url(),
        })

    return results



def get_search_results(query='', mode='', sort='', filter_form=None):
    """
    Used by bookmarker.views.search.
    Expects a dict:
    """
    if len(query) < 3:
        raise BadQueryException

    if mode and sort in SORTS[mode]:
        ORDERING[mode] = sort

    # Split out the meta options. TODO
    term = re.escape(query)
    # If the whole term is in quotation marks, assume word boundaries.
    if term.startswith('"') and term.endswith('"'):
        query = term.strip('"')
        term = r'\y{}\y'.format(query)

    notes = Note.objects.filter(
        Q(subject__iregex=term) |
        Q(quote__iregex=term) |
        Q(comment__iregex=term)
    )
    terms = TermOccurrence.objects.filter(
        Q(term__text__iregex=term) |
        Q(term__definition__iregex=term) |
        Q(quote__iregex=term) |
        Q(quote__iregex=term)
    )
    sections = Section.objects.filter(
        Q(title__iregex=term) |
        Q(subtitle__iregex=term) |
        Q(summary__iregex=term)
    )
    books = Book.objects.filter(
        Q(title__iregex=term) |
        Q(summary__iregex=term) |
        Q(details__authors__name__iregex=term)
    )

    # Add the sections where the author name matches BUT the associated books
    # not already in the books queryset above.
    book_pks = books.values_list('pk', flat=True)
    authors = Author.objects.filter(name__icontains=term)
    for author in authors:
        author_sections = author.sections.exclude(book_id__in=book_pks)
        if author_sections.exists():
            sections |= author_sections

    results = {
        'notes': notes,
        'terms': terms,
        'sections': sections,
        'books': books,
    }

    filters = {}
    filters_dict = {}
    if mode:
        # Now do the prefetching (only for expansion mode).
        to_prefetch = {
            'notes': [
                'book', 'section',
                'section__authors', 'book__details__default_authors', 'authors', 'tags',
            ],
            'terms': [
                'book', 'term', 'category', 'section',
                'section__authors', 'book__details__default_authors', 'authors',
            ],
            'sections': [
                'book',
                'authors', 'book__details__default_authors',
            ],
            'books': [
                'details__default_authors',
            ],
        }
        results[mode] = results[mode].prefetch_related(*to_prefetch[mode])

        if filter_form is not None:
            # If we're in a specific mode, update the filter_form - the dropdown options should reflect the results.
            # First, the authors dropdown.
            author_field_name = 'details__authors' if mode == 'books' else 'authors'
            author_pks = [
                i for l in results[mode].values_list(author_field_name) for i in l if i
            ]
            filter_form.fields['author'].queryset = Author.objects.filter(
                pk__in=author_pks
            )

            # Only show the books dropdown if the mode is not books.
            if mode != 'books':
                book_pks = [i['book_id'] for i in results[mode].values('book_id')]
                filter_form.fields['book'].queryset = Book.objects.filter(
                    pk__in=book_pks
                )

            # Only show section if the mode is not books or sections.
            if mode not in ('books', 'sections'):
                section_pks = [i['section_id'] for i in results[mode].values('section_id')]
                filter_form.fields['section'].queryset = Section.objects.filter(
                    pk__in=section_pks
                ).select_related('book')

            # Apply the filters, if any.
            if filter_form.is_valid():
                for filter_key in MODE_FILTERS[mode]:
                    if filter_form.cleaned_data[filter_key]:
                        filter_field = FILTER_FIELDS[filter_key]
                        # The Book model uses some different field names.
                        if mode == 'books' and filter_key in BOOK_FILTER_FIELDS:
                            filter_field = BOOK_FILTER_FIELDS[filter_key]
                        filters[filter_field] = filter_form.cleaned_data[filter_key]
                        filters_dict[filter_key] = filter_form.data[filter_key]

        # If sections, show the term/note counts.
        if mode == 'sections':
            results[mode] = results[mode].annotate(
                num_terms=Count('terms', distinct=True),
                num_notes=Count('notes', distinct=True),
            )

        if filters:
            # Make sure to prefetch again for the filtered queryset.
            results[mode] = results[mode].filter(
                **filters
            ).prefetch_related(
                *to_prefetch[mode]
            )
    else:
        results['terms'] = results['terms'].select_related('book', 'term')
        results['notes'] = results['notes'].select_related('book')
        results['sections'] = results['sections'].select_related('book')

    for key in results:
        results[key] = results[key].order_by(ORDERING[key]).distinct()

    return results, filters_dict
