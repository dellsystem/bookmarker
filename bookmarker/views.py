import collections
import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from books.api import CLIENT
from books.forms import NoteForm, SectionForm, ArtefactAuthorForm
from books.models import Book, Author, Note, NoteTag, Section
from vocab.api import lookup_term
from vocab.forms import TermForm, TermOccurrenceForm
from vocab.models import Term, TermOccurrence


def home(request):
    books = Book.objects.filter(is_processed=False).order_by(
        'is_processed', 'completed_sections', '-pk'
    ).annotate(
        num_terms=Count('terms', distinct=True),
        num_notes=Count('notes', distinct=True),
    ).prefetch_related('default_authors')

    context = {
        'started_books': books.filter(
            completed_sections=True
        ),
        'new_books': books.filter(
            completed_sections=False,
            completed_read=True,
        ),
        'unread_books': books.filter(completed_read=False),
        'complete_books': Book.objects.filter(is_processed=True),
    }
    return render(request, 'home.html', context)


def view_complete(request):
    books = Book.objects.filter(is_processed=True).annotate(
        num_notes=Count('notes', distinct=True),
        num_terms=Count('terms', distinct=True),
    ).prefetch_related('default_authors').order_by('-pk')

    context = {
        'books': books,
    }
    return render(request, 'view_complete.html', context)


def view_book(request, book_id):
    book = Book.objects.get(pk=book_id)

    recent_terms = book.terms.order_by('-added')[:5].prefetch_related(
        'term', 'category', 'section'
    )
    recent_notes = book.notes.order_by('-added')[:5]

    sections = book.sections.all().prefetch_related(
        'authors', 'book__default_authors'
    ).annotate(
        num_terms=Count('terms', distinct=True),
        num_notes=Count('notes', distinct=True),
    )

    context = {
        'book': book,
        'recent_terms': recent_terms,
        'recent_notes': recent_notes,
        'sections': sections,
    }
    return render(request, 'view_book.html', context)


def view_terms(request, book_id):
    book = Book.objects.get(pk=book_id)
    terms = book.terms.all().prefetch_related(
        'category', 'term', 'authors', 'section', 'section__authors', 'book',
        'book__default_authors',
    )

    author_pk = request.GET.get('author')
    try:
        author = Author.objects.get(pk=author_pk)
    except Author.DoesNotExist:
        author = None

    if author:
        terms = terms.filter(authors=author)

    paginator = Paginator(terms, 10)
    page = request.GET.get('page')
    try:
        terms = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        terms = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        terms = paginator.page(paginator.num_pages)

    context = {
        'book': book,
        'terms': terms,
        'author': author,
    }
    return render(request, 'view_terms.html', context)


@staff_member_required
def add_section(request, book_id):
    book = Book.objects.get(pk=book_id)
    if book.completed_sections:
        messages.error(request, 'Sections are already completed!')
        return redirect(book)

    new_form = True
    if request.method == 'POST':
        section_form = SectionForm(request.POST, prefix='section')
        author_form = ArtefactAuthorForm(request.POST, prefix='author')

        if section_form.is_valid() and author_form.is_valid():
            section = section_form.save(author_form, book=book)
            messages.success(request, u'Added section: {}'.format(section.title))
        else:
            new_form = False
            messages.error(request, 'Failed to add section')

    if new_form:
        section_form = SectionForm(prefix='section')
        author_form = ArtefactAuthorForm(prefix='author')

    context = {
        'book': book,
        'section_form': section_form,
        'author_form': author_form,
    }

    return render(request, 'add_section.html', context)


@staff_member_required
def edit_occurrence(request, occurrence_id):
    occurrence = TermOccurrence.objects.get(pk=occurrence_id)

    if request.POST:
        term_form = TermForm(
            request.POST,
            instance=occurrence.term,
            prefix='term',
        )
        author_form = ArtefactAuthorForm(
            request.POST,
            prefix='author',
        )
        occurrence_form = TermOccurrenceForm(
            request.POST,
            instance=occurrence,
            prefix='occurrence',
        )
        if (
                term_form.is_valid() and
                author_form.is_valid() and
                occurrence_form.is_valid()
        ):
            occurrence_form.save(author_form)
            occurrence.term.definition = term_form.cleaned_data['definition']
            occurrence.term.highlights = term_form.cleaned_data['highlights']
            occurrence.term.save()
            messages.success(request, 'Theoretically worked')
            return redirect(occurrence)
        else:
            messages.error(request, 'Failed to save term')
    else:
        term_form = TermForm(
            instance=occurrence.term,
            prefix='term',
        )
        author_form = ArtefactAuthorForm(
            prefix='author',
            initial=occurrence.get_author_data(),
        )
        occurrence_form = TermOccurrenceForm(
            instance=occurrence,
            prefix='occurrence',
            initial={
                'page_number': occurrence.get_page_display(),
            }
        )

    context = {
        'occurrence': occurrence,
        'book': occurrence.book,
        'term_form': term_form,
        'occurrence_form': occurrence_form,
        'author_form': author_form,
        'term': occurrence.term,
    }

    return render(request, 'edit_occurrence.html', context)


@staff_member_required
def add_term(request, book_id):
    book = Book.objects.get(pk=book_id)

    if not book.completed_sections:
        messages.error(request, 'Sections need to be completed first')
        return redirect(book)

    new_forms = True
    if request.method == 'POST':
        term_form = TermForm(request.POST, prefix='term')
        occurrence_form = TermOccurrenceForm(request.POST, book=book, prefix='occurrence')
        author_form = ArtefactAuthorForm(request.POST, prefix='author')

        if (
                term_form.is_valid() and
                occurrence_form.is_valid() and
                author_form.is_valid()
        ):
            term, created = Term.objects.get_or_create(
                text=term_form.cleaned_data['text'],
                language=term_form.cleaned_data['language'],
                defaults={
                    'definition': term_form.cleaned_data['definition'],
                    'highlights': term_form.cleaned_data['highlights'],
                },
            )
            if not created:
                term.definition = term_form.cleaned_data['definition']
                term.highlights = term_form.cleaned_data['highlights']
                term.save()

            occurrence = occurrence_form.save(author_form, term=term)

            if occurrence.section:
                message = u'Added term {term} to section {section}'.format(
                    term=term.text,
                    section=occurrence.section.title,
                )
            else:
                message = u'Added term: {}'.format(term.text)

            messages.success(request, message)
        else:
            new_forms = False
            messages.error(request, 'Failed to add term')

    if new_forms:
        term_form = TermForm(
            initial={'language': book.language},
            prefix='term',
        )
        occurrence_form = TermOccurrenceForm(
            prefix='occurrence',
            book=book,
        )
        author_form = ArtefactAuthorForm(
            prefix='author',
        )

    recent_terms = book.terms.order_by('-added')
    context = {
        'book': book,
        'recent_terms_1': recent_terms[:3],
        'recent_terms_2': recent_terms[3:6],
        'term_form': term_form,
        'occurrence_form': occurrence_form,
        'author_form': author_form,
    }

    return render(request, 'add_term.html', context)


@staff_member_required
def add_author(request):
    goodreads_id = request.POST.get('goodreads_id')
    gr_author = CLIENT.author(goodreads_id)

    try:
        author = Author.objects.get(goodreads_id=goodreads_id)
    except Author.DoesNotExist:
        author = Author.objects.create(
            goodreads_id=goodreads_id,
            name=gr_author.name,
            link=gr_author.link,
        )
        messages.success(
            request,
            u'Added author: {}'.format(author.name),
        )

    return redirect(author)


@staff_member_required
def add_book(request):
    goodreads_id = request.POST.get('goodreads_id')
    gr_book = CLIENT.book(goodreads_id)

    try:
        book = Book.objects.get(goodreads_id=goodreads_id)
    except Book.DoesNotExist:
        book = Book.objects.create(
            goodreads_id=goodreads_id,
            title=gr_book.title,
            image_url=gr_book.image_url,
            link=gr_book.link
        )
        messages.success(
            request,
            u'Added book: {}'.format(book.title),
        )

        for gr_author in gr_book.authors:
            try:
                author = Author.objects.get(goodreads_id=gr_author.gid)
            except Author.DoesNotExist:
                author = None

            if author is None:
                author = Author.objects.create(
                    goodreads_id=gr_author.gid,
                    name=gr_author.name,
                    link=gr_author.link,
                )
                messages.success(
                    request,
                    u'Added author: {}'.format(author.name),
                )

            book.authors.add(author)
            book.default_authors.add(author)

    return redirect(book)


def suggest_terms(request):
    term = request.GET.get('term')

    # Find terms of all languages that start with these characters.
    if term and len(term) >= 3:
        terms = Term.objects.filter(text__icontains=term).values(
            'text', 'language'
        )

    return JsonResponse({
        'terms': list(terms)[:5],
    })


def get_definition(request):
    term = request.GET.get('term', '')
    language = request.GET.get('language', 'en')

    view_link = None
    definition = None
    highlights = None
    num_occurrences = 0

    if term and language:
        # Check if the term already exists.
        try:
            existing_term = Term.objects.get(text=term, language=language)
        except Term.DoesNotExist:
            existing_term = None

        if existing_term:
            definition = existing_term.definition
            view_link = reverse('view_term', args=[existing_term.pk])
            highlights = existing_term.highlights
            num_occurrences = existing_term.occurrences.count()
        else:
            definition = lookup_term(language, term)
            highlights = term.lower().replace('-', ' ')

    return JsonResponse({
        'term': term,
        'language': language,
        'definition': definition,
        'highlights': highlights,
        'view_link': view_link,
        'num_occurrences': num_occurrences,
    })


@staff_member_required
def add_note(request, book_id):
    book = Book.objects.get(pk=book_id)

    if not book.completed_sections:
        messages.error(request, 'Sections need to be completed first')
        return redirect(book)

    new_form = True
    if request.method == 'POST':
        note_form = NoteForm(request.POST, prefix='note', book=book)
        author_form = ArtefactAuthorForm(request.POST, prefix='author')

        if note_form.is_valid() and author_form.is_valid():
            note = note_form.save(author_form)

            if note.section:
                message = u'Added note {note} to section {section}'.format(
                    note=note.subject,
                    section=note.section.title,
                )
            else:
                message = u'Added note: {}'.format(note.subject)

            messages.success(request, message)
        else:
            new_form = False
            messages.error(request, 'Failed to add note')

    if new_form:
        note_form = NoteForm(prefix='note', book=book)
        author_form = ArtefactAuthorForm(prefix='author')

    recent_notes = book.notes.order_by('-added')
    context = {
        'book': book,
        'note_form': note_form,
        'author_form': author_form,
        'recent_notes_1': recent_notes[:3],
        'recent_notes_2': recent_notes[3:6],
    }

    return render(request, 'add_note.html', context)


def view_all_authors(request):
    books_by_pk = {book.pk: book for book in Book.objects.all()}
    authors = Author.objects.all().prefetch_related('books', 'sections')

    authors_and_books = []
    for author in authors:
        author_books = [books_by_pk[b] for b in author.get_associated_books()]
        authors_and_books.append((author, author_books))

    context = {
        'authors_and_books': authors_and_books,
    }

    return render(request, 'view_all_authors.html', context)


def view_all_notes(request):
    notes = Note.objects.order_by('book').select_related('book').prefetch_related(
        'authors', 'tags', 'section', 'section__authors', 'book__default_authors'
    )

    commented = request.GET.get('commented')
    if commented:
        notes = notes.exclude(comment='')
    untagged = request.GET.get('untagged')
    if untagged:
        notes = notes.filter(tags=None)

    author_pk = request.GET.get('author')
    try:
        author = Author.objects.get(pk=author_pk)
    except Author.DoesNotExist:
        author = None

    if author:
        notes = notes.filter(authors=author)

    paginator = Paginator(notes, 10)
    page = request.GET.get('page')
    try:
        notes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        notes = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        notes = paginator.page(paginator.num_pages)

    context = {
        'notes': notes,
        'author': author,
    }

    return render(request, 'view_all_notes.html', context)


def view_notes(request, book_id):
    book = Book.objects.get(pk=book_id)
    notes = book.notes.all().prefetch_related(
        'tags', 'authors', 'section', 'section__authors', 'book',
        'book__default_authors',
    )

    author_pk = request.GET.get('author')
    try:
        author = Author.objects.get(pk=author_pk)
    except Author.DoesNotExist:
        author = None

    if author:
        notes = notes.filter(authors=author)

    paginator = Paginator(notes, 10)
    page = request.GET.get('page')
    try:
        notes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        notes = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        notes = paginator.page(paginator.num_pages)

    context = {
        'book': book,
        'notes': notes,
        'author': author,
    }

    return render(request, 'view_notes.html', context)


def view_note(request, note_id):
    note = Note.objects.get(pk=note_id)
    query = request.GET.get('q')

    context = {
        'book': note.book,
        'note': note,
        'query': query,
    }

    return render(request, 'view_note.html', context)


def view_occurrence(request, occurrence_id):
    occurrence = TermOccurrence.objects.get(pk=occurrence_id)
    query = request.GET.get('q')

    context = {
        'occurrence': occurrence,
        'term': occurrence.term,
        'book': occurrence.book,
        'query': query,
    }

    return render(request, 'view_occurrence.html', context)


def view_term(request, term_id):
    term = Term.objects.get(pk=term_id)
    query = request.GET.get('q')
    occurrences = term.occurrences.order_by('book__title').prefetch_related(
        'book', 'authors', 'book__default_authors', 'category', 'section',
        'section__authors',
    )
    context = {
        'term': term,
        'occurrences': occurrences,
        'query': query,
    }

    return render(request, 'view_term.html', context)


def view_author(request, author_id):
    author = Author.objects.get(pk=author_id)
    author_section_ids = set()
    book_ids = set()

    # Find all the books for which the author has some sections.
    sections_by_book = collections.defaultdict(list)
    for section in author.sections.all().prefetch_related('authors', 'book__default_authors'):
        book_id = section.book_id
        book_ids.add(book_id)

        sections_by_book[book_id].append(section)
        author_section_ids.add(section.pk)

    # Find books for which the author is not listed as an author but has
    # associated terms or notes.
    notes_by_book = collections.defaultdict(list)
    for note in author.notes.all():
        book_id = note.book_id

        section_id = note.section_id
        if section_id:
            if section_id in author_section_ids:
                continue

        book_ids.add(book_id)

        notes_by_book[book_id].append(note)

    terms_by_book = collections.defaultdict(list)
    for term in author.terms.all().prefetch_related('category', 'term'):
        book_id = term.book_id

        section_id = term.section_id
        if section_id:
            if section_id in author_section_ids:
                continue

        book_ids.add(book_id)

        terms_by_book[book_id].append(term)

    books_query = Book.objects.filter(pk__in=book_ids).prefetch_related(
        'default_authors'
    )

    books = []
    for book in books_query:
        # Only show notes if there are no sections.
        book_sections = sections_by_book[book.id]
        book_notes = notes_by_book[book.id]
        book_terms = terms_by_book[book.id]

        books.append({
            'book': book,
            'sections': book_sections,
            'notes': book_notes[:5],
            'terms': book_terms[:5],
            'num_notes': len(book_notes),
            'num_terms': len(book_terms),
        })

    context = {
        'author': author,
        'books': books,
        'num_terms': author.terms.count(),
        'num_notes': author.notes.count(),
    }

    return render(request, 'view_author.html', context)


def view_all_terms(request):
    occurrences = TermOccurrence.objects.order_by('term').prefetch_related(
        'term', 'book', 'book__default_authors', 'authors', 'section',
        'section__authors', 'category'
    ) # could still be optimised further

    author_pk = request.GET.get('author')
    try:
        author = Author.objects.get(pk=author_pk)
    except Author.DoesNotExist:
        author = None

    if author:
        occurrences = occurrences.filter(authors=author)

    paginator = Paginator(occurrences, 10)
    page = request.GET.get('page')
    try:
        occurrences = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        occurrences = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        occurrences = paginator.page(paginator.num_pages)

    context = {
        'occurrences': occurrences,
        'author': author,
    }

    return render(request, 'view_all_terms.html', context)


@staff_member_required
@require_POST
def mark_complete(request, book_id):
    book = Book.objects.get(pk=book_id)

    mode = request.POST.get('mode')
    if mode == 'processed':
        if book.is_processed:
            messages.error(request, 'Book already marked as processed')
        else:
            book.is_processed = True
            book.save()
            messages.success(request, 'Book marked as processed')
    elif mode == 'sections':
        if book.completed_sections:
            messages.error(request, 'Sections already marked as complete')
        else:
            book.completed_sections = True
            book.save()
            messages.success(request, 'Sections marked as complete')
    else:
        messages.error(request, 'Invalid mode: {}'.format(mode))

    return redirect(book)


@staff_member_required
def edit_section(request, section_id):
    section = Section.objects.get(pk=section_id)

    if request.method == 'POST':
        section_form = SectionForm(
            request.POST, instance=section, prefix='section'
        )
        author_form = ArtefactAuthorForm(
            request.POST, prefix='author',
        )
        if section_form.is_valid() and author_form.is_valid():
            section = section_form.save(author_form)

            messages.success(
                request, u'Edited section: {}'.format(section.title)
            )
            return redirect(section.book)
        else:
            messages.error(request, 'Failed to save section')
    else:
        section_form = SectionForm(
            instance=section,
            prefix='section',
            initial={
                'page_number': section.get_page_display(),
            }
        )

        author_form = ArtefactAuthorForm(
            prefix='author',
            initial=section.get_author_data(),
        )

    context = {
        'section': section,
        'book': section.book,
        'section_form': section_form,
        'author_form': author_form,
    }

    return render(request, 'edit_section.html', context)


def view_section(request, section_id):
    section = Section.objects.get(pk=section_id)

    # Find the previous and next sections (if any) for this book.
    # TODO: Is there a better way to do this? get_next_by is only for DateField

    context = {
        'book': section.book,
        'section': section,
        'previous_section': section.get_previous(),
        'next_section': section.get_next(),
    }

    return render(request, 'view_section.html', context)


def search(request):
    query = request.GET.get('q')

    MODES = ('notes', 'terms', 'sections', 'books')
    mode = request.GET.get('mode')
    if mode not in MODES:
        mode = None

    # Split out the meta options. TODO
    term = query

    results = {
        'notes': Note.objects.filter(
            Q(subject__icontains=term) |
            Q(quote__icontains=term) |
            Q(comment__icontains=term)
        ).order_by('book').select_related('book').prefetch_related(
            'section__authors', 'book__default_authors', 'authors', 'tags',
        ),
        'terms': TermOccurrence.objects.filter(
            Q(term__text__icontains=term) |
            Q(term__definition__icontains=term) |
            Q(quote__icontains=term) |
            Q(quote__icontains=term)
        ).select_related(
            'term', 'book', 'category', 'section'
        ).prefetch_related(
            'section__authors', 'book__default_authors', 'authors'
        ).order_by('term'),
        'sections': Section.objects.filter(
            Q(title__icontains=term) |
            Q(subtitle__icontains=term) |
            Q(summary__icontains=term)
        ).order_by('book').select_related('book').prefetch_related(
            'authors', 'book__default_authors',
        ),
        'books': Book.objects.filter(
            Q(title__icontains=term) |
            Q(summary__icontains=term) |
            Q(authors__name__icontains=term)
        ).prefetch_related('authors'),
    }

    context = {
        'results': results,
        'query': query,
        'mode': mode,
        'modes': MODES,
        'qs': '?q=' + query,
    }

    return render(request, 'search.html', context)


def view_stats(request):
    shelf = CLIENT.user(60292716).shelves()[2]
    num_to_read = shelf.count

    # Estimate the end date.
    num_per_year = 208
    days_left = num_to_read / float(num_per_year) * 365
    end_date = datetime.datetime.today() + datetime.timedelta(days=days_left)

    context = {
        'num_to_read': num_to_read,
        'end_date': end_date,
    }

    return render(request, 'view_stats.html', context)


@staff_member_required
def edit_note(request, note_id):
    note = Note.objects.get(pk=note_id)

    if request.method == 'POST':
        note_form = NoteForm(request.POST, instance=note, prefix='note')
        author_form = ArtefactAuthorForm(request.POST, prefix='author')
        if note_form.is_valid() and author_form.is_valid():
            note = note_form.save(author_form)
            messages.success(
                request, u'Edited note: {}'.format(note.subject)
            )
            return redirect(note)
        else:
            messages.error(request, 'Failed to save note')
    else:
        note_form = NoteForm(
            instance=note,
            prefix='note',
            initial={
                'page_number': note.get_page_display(),
            }
        )

        author_form = ArtefactAuthorForm(
            prefix='author',
            initial=note.get_author_data(),
        )

    context = {
        'note': note,
        'book': note.book,
        'note_form': note_form,
        'author_form': author_form,
    }

    return render(request, 'edit_note.html', context)


def view_tag(request, slug):
    tag = NoteTag.objects.get(slug=slug)

    notes = tag.notes.order_by('book').prefetch_related(
        'authors', 'section__authors', 'tags', 'book', 'book__default_authors',
    )
    paginator = Paginator(notes, 10)
    page = request.GET.get('page')
    try:
        notes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        notes = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        notes = paginator.page(paginator.num_pages)

    context = {
        'tag': tag,
        'notes': notes,
    }

    return render(request, 'view_tag.html', context)


def view_all_tags(request):
    tags = NoteTag.objects.all()

    context = {
        'tags': tags,
    }

    return render(request, 'view_all_tags.html', context)
