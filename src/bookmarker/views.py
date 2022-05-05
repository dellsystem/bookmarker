import collections
import datetime
import random
from dateutil import parser

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Q, Count
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from activity.models import Action, CATEGORIES, FILTER_CATEGORIES
from books import goodreadstools, redistools, highlighter
from books.forms import NoteForm, SectionForm, ArtefactAuthorForm, BookForm, \
                        BookDetailsForm, AuthorForm, TagForm, \
                        MultipleSectionsForm
from books.models import Book, Author, Note, Tag, Section, \
                         BookDetails, TagCategory, GoodreadsAuthor
from bookmarker.forms import SearchFilterForm
from vocab.api import lookup_term
from vocab.forms import TermForm, TermOccurrenceForm
from vocab.models import Term, TermOccurrence


class LoginView(auth_views.LoginView):
    template_name = "login.html"


class LogoutView(auth_views.LogoutView):
    pass


def home(request):
    actions_list = Action.objects.all()

    mode = request.GET.get('mode')
    if mode in FILTER_CATEGORIES:
        actions_list = actions_list.filter(category=mode)
    else:
        mode = 'all'

    paginator = Paginator(actions_list, 5)
    page = request.GET.get('page')
    try:
        paged_actions = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paged_actions = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        paged_actions = paginator.page(paginator.num_pages)

    all_books = Book.objects.order_by(
        'is_processed', 'completed_sections', '-pk'
    ).annotate(
        num_terms=Count('terms', distinct=True),
        num_notes=Count('notes', distinct=True),
    ).prefetch_related('details__default_authors')

    books = {
        'complete': all_books.filter(is_processed=True),
        'new': all_books.filter(
            is_processed=False,
            completed_sections=False,
            completed_read=True,
            details__isnull=False,
        ),
        'unread': all_books.filter(completed_read=False),
        'incomplete': all_books.filter(
            completed_sections=True,
            is_processed=False,
        ),
        'publications': all_books.filter(
            details__isnull=True
        ),
    }

    # Hide the book info for actions that have the same book as the preceding
    # action.
    previous_book_id = None
    actions = []
    for action in paged_actions:
        show_book = action.book_id != previous_book_id
        actions.append((action, show_book))
        previous_book_id = action.book_id

    # Create a sorted list of available categories (with associated icon).
    filter_categories = [
        (c, CATEGORIES[c]['icon']) for c in FILTER_CATEGORIES
    ]
    context = {
        'books': books,
        'actions': actions,
        'paged_actions': paged_actions,
        'mode': mode,
        'filter_categories': filter_categories,
    }
    return render(request, 'activity.html', context)


def view_books(request, book_type):
    all_books = Book.objects.order_by(
        'is_processed', 'completed_sections', '-pk'
    ).annotate(
        num_terms=Count('terms', distinct=True),
        num_notes=Count('notes', distinct=True),
    ).prefetch_related('details__default_authors')

    books = {
        'new': all_books.filter(
            is_processed=False,
            completed_sections=False,
            completed_read=True,
            details__isnull=False,
        ).order_by('-details__end_date'),
        'incomplete': all_books.filter(
            completed_sections=True,
            is_processed=False,
        ),
        'unread': all_books.filter(completed_read=False).order_by(
            F('details__due_date').asc(nulls_last=True),
            F('details__priority').asc(nulls_last=True)
        ),
        'publications': all_books.filter(
            details__isnull=True
        ),
        'complete': all_books.filter(is_processed=True),
    }
    if book_type not in books:
        book_type = 'complete'
        messages.warning(request, 'Invalid book type - showing completed')

    context = {
        'books': books,
        'book_type': book_type,
        'displayed_books': books[book_type],
    }
    return render(request, 'view_books.html', context)


def view_book(request, slug):
    book = get_object_or_404(Book, slug=slug)

    recent_terms = book.terms.order_by('-added')[:5].prefetch_related(
        'term', 'category', 'section'
    )
    recent_notes = book.notes.order_by('-added')[:5]

    sections = book.sections.all().prefetch_related(
        'authors', 'book__details__default_authors'
    ).annotate(
        num_terms=Count('terms', distinct=True),
        num_notes=Count('notes', distinct=True),
    )

    # If it's a publication, order the articles alphabetically by name.
    if book.details is None:
        sections = sections.order_by('title')

    context = {
        'book': book,
        'details': book.details,
        'recent_terms': recent_terms,
        'recent_notes': recent_notes,
        'sections': sections,
    }
    return render(request, 'view_book.html', context)


@login_required
def edit_book(request, slug):
    book = get_object_or_404(Book, slug=slug)

    if request.method == 'POST':
        book_form = BookForm(request.POST, instance=book)

        if book.details:
            details_form = BookDetailsForm(request.POST, instance=book.details)
        else:
            details_form = None

        if book_form.is_valid() and (details_form is None or details_form.is_valid()):
            book_form.save()
            if details_form:
                details_form.save()
                book.details.save()

            Action.objects.create(
                category='book',
                verb='edited',
                details=book.title,
                primary_id=book.pk,
            )
            messages.success(request, u'Edited book: {}'.format(book.title))
            return redirect(book)
        else:
            messages.error(request, 'Failed to edit book')
    else:
        book_form = BookForm(instance=book)
        if book.details:
            details_form = BookDetailsForm(instance=book.details)
        else:
            details_form = None

    context = {
        'book': book,
        'book_form': book_form,
        'details_form': details_form,
    }

    return render(request, 'edit_book.html', context)


def view_terms(request, slug):
    book = get_object_or_404(Book, slug=slug)
    terms = book.terms.all().prefetch_related(
        'category', 'term', 'authors', 'section', 'section__authors', 'book',
        'book__details__default_authors',
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


@login_required
def add_section(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if book.completed_sections:
        messages.error(request, 'Sections are already completed!')
        return redirect(book)

    new_form = True
    if request.method == 'POST':
        section_form = SectionForm(book, request.POST, prefix='section')
        author_form = ArtefactAuthorForm(request.POST, prefix='author')

        if section_form.is_valid() and author_form.is_valid():
            section = section_form.save(author_form)
            messages.success(request, u'Added section: {}'.format(section.title))

            Action.objects.create(
                primary_id=section.pk,
                category='section',
                verb='added',
                details=section.title,
                secondary_id=section.book.pk,
            )

            # If it's a publication, go straight to that section's page.
            if not book.details:
                return redirect(section)
        else:
            new_form = False
            messages.error(request, 'Failed to add section')

    if new_form:
        section_initial = {}

        predict_number = True
        # If the book is a periodical, it won't have chapter numbers.
        if book.details and book.details.issue_number:
            predict_number = False

        # If at least 2 sections exist and none have numbers, give up.
        if (
                book.sections.count() >= 2 and
                not book.sections.filter(number__isnull=False).exists()
        ):
            predict_number = False

        if predict_number:
            section_initial['number'] = (
                book.sections.filter(number__gt=0).count() + 1
            )

        section_form = SectionForm(
            book, prefix='section', initial=section_initial
        )

        # If the book is an edited collection, set the author mode to custom.
        author_initial = {}
        if book.details and book.details.is_edited or not book.details:
            author_initial['mode'] = 'custom'
        author_form = ArtefactAuthorForm(prefix='author', initial=author_initial)

    sections = book.sections.prefetch_related(
        'authors', 'book__details__default_authors',
    )

    context = {
        'book': book,
        'sections': sections,
        'section_form': section_form,
        'author_form': author_form,
    }

    return render(request, 'add_section.html', context)


@login_required
def add_sections(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if book.completed_sections:
        messages.error(request, 'Sections are already completed!')
        return redirect(book)

    if request.method == 'POST':
        form = MultipleSectionsForm(request.POST)

        if form.is_valid():
            section_data = form.cleaned_data['sections']
            for s in section_data:
                section = Section.objects.create(
                    book=book,
                    number=s['number'],
                    page_number=s['page_number'],
                    in_preface=s['in_preface'],
                    title=s['title'],
                )
                if book.details:
                    section.authors.add(*book.details.default_authors.all())

                Action.objects.create(
                    primary_id=section.pk,
                    category='section',
                    verb='added',
                    details=s['title'],
                    secondary_id=book.pk,
                )

            messages.success(request, u'Added {} sections'.format(len(section_data)))

            return redirect(book)
        else:
            messages.error(request, 'Failed to add sections')
    else:
        form = MultipleSectionsForm()

    sections = book.sections.prefetch_related(
        'authors', 'book__details__default_authors',
    )

    context = {
        'book': book,
        'sections': sections,
        'form': form,
    }

    return render(request, 'add_sections.html', context)


@login_required
def edit_occurrence(request, occurrence_id):
    occurrence = get_object_or_404(TermOccurrence, pk=occurrence_id)

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
            occurrence.book,
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
            messages.success(request, 'Edited term occurrence: {}'.format(
                occurrence.term.text
            ))
            Action.objects.create(
                category='term',
                verb='edited',
                primary_id=occurrence.pk,
                secondary_id=occurrence.book.pk,
                details=occurrence.term.text,
            )
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
            occurrence.book,
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


@login_required
def add_term(request, slug):
    book = get_object_or_404(Book, slug=slug)

    if not book.completed_sections and book.details:
        messages.error(request, 'Sections need to be completed first')
        return redirect(book)

    new_forms = True
    if request.method == 'POST':
        term_form = TermForm(request.POST, prefix='term')
        occurrence_form = TermOccurrenceForm(book, request.POST, prefix='occurrence')
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

            Action.objects.create(
                category='term',
                verb='added',
                primary_id=occurrence.pk,
                secondary_id=occurrence.book.pk,
                details=term.text,
            )
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
            book,
            prefix='occurrence',
        )
        author_form = ArtefactAuthorForm(
            prefix='author',
        )

    recent_terms = book.terms.order_by('-added').prefetch_related('category', 'term')
    context = {
        'book': book,
        'recent_terms_1': recent_terms[:3],
        'recent_terms_2': recent_terms[3:6],
        'term_form': term_form,
        'occurrence_form': occurrence_form,
        'author_form': author_form,
    }

    return render(request, 'add_term.html', context)

@require_POST
@login_required
def add_author_from_id(request):
    query = request.POST.get('q')

    # If the query parameter is missing, show the form.
    if not query:
        return redirect('add_author')

    # If there's a : in the goodreads ID, then it's being sent from the keyboard shortcut modal. 
    if ':' in query:
        # Extract the goodreads ID from the posted parameter.
        goodreads_id = query.split(':')[0]
    else:
        goodreads_id = query

    # See if author already exists.
    gr_author = GoodreadsAuthor.objects.filter(goodreads_id=goodreads_id)
    if gr_author.exists():
        messages.error(request, 'Author for ID {} already exists'.format(goodreads_id))
        return redirect(gr_author.first().author)

    # Author doesn't exist - fetch from goodreads api
    author_data = goodreadstools.get_author_by_id(goodreads_id)
    author = Author.objects.create_from_goodreads(author_data)

    Action.objects.create(
        category='author',
        primary_id=author.pk,
        verb='added',
        details=author.name,
    )
    messages.success(request, 'Added author: {}'.format(author.name))

    return redirect(author)

@login_required
def add_author(request):
    if request.POST.get('submit'):
        author_form = AuthorForm(request.POST)

        if author_form.is_valid():
            author = author_form.save()

            Action.objects.create(
                category='author',
                primary_id=author.pk,
                details=author.name,
                verb='added',
            )
            messages.success(request, 'Added author: %s' % author.name)
            return redirect(author)
        else:
            messages.error(
                request,
                'Error creating author'
            )
    else:
        author_form = AuthorForm()

    context = {
        'author_form': author_form,
    }

    return render(request, 'add_author.html', context)


@require_POST
@login_required
def add_book_from_id(request):
    query = request.POST.get('q')

    # If the query parameter is missing, show the form.
    if not query:
        return redirect('add_book')

    # If there's a : in the goodreads ID, then it's being sent from the keyboard shortcut modal. 
    if ':' in query:
        # Extract the goodreads ID from the posted parameter.
        goodreads_id = query.split(':')[0]
    else:
        goodreads_id = query

    # Check if book already exists.
    book_qs = Book.objects.filter(details__goodreads_id=goodreads_id)
    if book_qs.exists():
        messages.error(request, 'Book for ID {} already exists'.format(goodreads_id))
        return redirect(book_qs.first())

    # Book doesn't exist, so get from goodreads api (or redis cache, if it exists).
    book_data = goodreadstools.get_book_by_id(goodreads_id)
    book = Book.objects.create_from_goodreads(book_data)

    messages.success(request, 'Added book: {}'.format(book.title))

    for author_data in book_data['authors']:
        gr_author = GoodreadsAuthor.objects.filter(
            goodreads_id=author_data['id']
        )
        if gr_author.exists():
            author = gr_author.first().author
        else:
            # Author doesn't exist yet - must create.
            author = Author.objects.create_from_goodreads(author_data)
            messages.success(request, 'Added author: {}'.format(author.name))

        book.details.authors.add(author)
        book.details.default_authors.add(author)

    return redirect(book)


@login_required
def add_book(request):
    if request.POST.get('submit'):
        book_form = BookForm(request.POST)

        if request.POST['submit'] == 'details':
            details_form = BookDetailsForm(request.POST)
        else:
            details_form = None

        if book_form.is_valid():
            book = book_form.save()

            Action.objects.create(
                category='book',
                primary_id=book.pk,
                details=book.title,
                verb='added',
            )

            if details_form:
                messages.error(request, 'Has details form')
                if details_form.is_valid():
                    details = details_form.save()
                    book.details = details
                    book.save()
                    messages.success(request, 'Added book with details')
                    return redirect(book)
                else:
                    messages.error(
                        request,
                        'Error with details form'
                    )
            else:
                messages.error(request, 'Does not have details form')
                messages.success(request, 'Added book')
                return redirect(book)
        else:
            messages.error(
                request,
                'Error with book form'
            )
    else:
        book_form = BookForm()
        details_form = BookDetailsForm()

    context = {
        'book_form': book_form,
        'details_form': details_form,
    }

    return render(request, 'add_book.html', context)


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


@login_required
def add_note(request, slug):
    section_id = request.GET.get('section')
    book = get_object_or_404(Book, slug=slug)

    # If the "book" is actually a publication, and there is no section passed
    # as a GET param, just use the most recently-added article/section.
    if not section_id and book.is_publication():
        latest_article = book.sections.latest('pk')
        if latest_article:
            section_id = latest_article.pk

    if not book.completed_sections and book.details:
        messages.error(request, 'Sections need to be completed first')
        return redirect(book)

    new_form = True
    if request.method == 'POST':
        note_form = NoteForm(book, request.POST, prefix='note')
        author_form = ArtefactAuthorForm(request.POST, prefix='author')

        if note_form.is_valid() and author_form.is_valid():
            note = note_form.save(author_form)
            Action.objects.create(
                primary_id=note.pk,
                category='note',
                verb='added',
                details=note.subject,
                secondary_id=note.book.pk,
            )

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
        initial = {}
        if section_id:
            initial['section'] = section_id

        note_form = NoteForm(book, prefix='note', initial=initial)
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
    authors = Author.objects.prefetch_related('sections', 'books', 'default_books')
    book_values_list = Book.objects.values_list('id', 'title', 'slug', 'details_id')
    book_data = {}
    details_ids = {}
    for book_id, book_title, book_slug, details_id in book_values_list:
        book_data[book_id] = {
            'title': book_title,
            'url': reverse('view_book', args=[book_slug]),
        }
        details_ids[details_id] = book_id

    authors_and_books = []
    for author in authors:
        # This is hacky (it should really be a method on the model) but
        # necessary for performance, as otherwise Django creates n queries
        # despite the use of prefetch_related. Hence the workaround with
        # details_ids, which helps avoid further lookups in this for loop.
        book_ids = set()
        for section in author.sections.all():
            book_ids.add(section.book_id)
        for details in author.books.all():
            book_id = details_ids.get(details.id)
            if book_id:
                book_ids.add(book_id)
        for details in author.default_books.all():
            book_id = details_ids.get(details.id)
            if book_id:
                book_ids.add(book_id)

        author_books = [book_data[book_id] for book_id in book_ids]
        authors_and_books.append((author, author_books))

    context = {
        'authors_and_books': authors_and_books,
    }

    return render(request, 'view_all_authors.html', context)


def view_all_notes(request):
    notes = Note.objects.select_related('book').prefetch_related(
        'authors', 'tags', 'section', 'section__authors', 'book__details__default_authors'
    ).order_by('book', 'added')

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


def view_notes(request, slug):
    book = get_object_or_404(Book, slug=slug)
    notes = book.notes.all().prefetch_related(
        'tags', 'authors', 'section', 'section__authors', 'book',
        'book__details__default_authors',
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
    note = get_object_or_404(Note, pk=note_id)
    book = note.book
    query = request.GET.get('q')

    # If it's a publication or edited book, limit to the section. Otherwise,
    # use the whole book.
    if book.details is None or book.details.is_edited:
        note_container = 'section'
        notes = Note.objects.filter(section=note.section)
    else:
        note_container = 'book'
        notes = Note.objects.filter(book=note.book)

    previous_note = None
    next_note = None
    found_note = False
    for n in notes:
        if found_note:
            next_note = n
            break
        elif n.pk != note.pk:
            previous_note = n

        if n.pk == note.pk:
            found_note = True

    context = {
        'note_count': notes.count(),
        'note_container': note_container,
        'previous_note': previous_note,
        'next_note': next_note,
        'book': book,
        'note': note,
        'query': query,
    }

    return render(request, 'view_note.html', context)


def view_occurrence(request, occurrence_id):
    occurrence = get_object_or_404(TermOccurrence, pk=occurrence_id)
    query = request.GET.get('q')

    context = {
        'occurrence': occurrence,
        'term': occurrence.term,
        'book': occurrence.book,
        'query': query,
    }

    return render(request, 'view_occurrence.html', context)


@require_POST
def flag_term(request, term_id):
    term = get_object_or_404(Term, pk=term_id)
    action = request.POST.get('action')
    if term.flagged and action == 'unflag':
        term.flagged = False
        term.save()
        messages.success(request, 'Term unflagged')
    elif not term.flagged and action == 'flag':
        term.flagged = True
        term.save()
        messages.success(request, 'Term flagged')
    else:
        messages.error(request, 'Term flag status not changed')

    return redirect(term)


def view_term(request, term_id):
    term = get_object_or_404(Term, pk=term_id)
    query = request.GET.get('q')
    occurrences = term.occurrences.order_by('book__title').prefetch_related(
        'book', 'authors', 'book__details__default_authors', 'category', 'section',
        'section__authors',
    )
    context = {
        'term': term,
        'occurrences': occurrences,
        'query': query,
    }

    return render(request, 'view_term.html', context)


def section_redirect(request, slug):
    section = get_object_or_404(Section, slug=slug)

    return redirect(section)


def view_author(request, slug):
    author = get_object_or_404(Author, slug=slug)
    author_section_ids = set()
    book_ids = set()

    # Find the author's direct books.
    for details in author.books.all().select_related('book'):
        if details.book:
            book_ids.add(details.book.pk)
    for details in author.default_books.all().select_related('book'):
        if details.book:
            book_ids.add(details.book.pk)

    # Find all the books for which the author has some sections.
    sections_by_book = collections.defaultdict(list)
    sections = author.sections.all().annotate(
        num_terms=Count('terms', distinct=True),
        num_notes=Count('notes', distinct=True),
    ).prefetch_related(
        'authors', 'book__details__default_authors',  'related_to__terms',
        'related_to__notes',
    ).select_related('related_to', 'related_to__book',)
    for section in sections:
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
        'details__default_authors'
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
    terms = Term.objects.order_by(Lower('text'))

    author_pk = request.GET.get('author')
    author = None
    if author_pk:
        try:
            author = Author.objects.get(pk=author_pk)
        except Author.DoesNotExist:
            pass

        if author:
            terms = terms.filter(occurrences__authors=author)

    flagged = request.GET.get('flagged')
    if flagged:
        terms = terms.filter(flagged=True)

    paginator = Paginator(terms, 25)
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
        'flagged': flagged,
        'terms': terms,
        'author': author,
    }

    return render(request, 'view_all_terms.html', context)


@login_required
@require_POST
def mark_complete(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

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


@login_required
def edit_section(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    if request.method == 'POST':
        if request.POST.get('submit') == 'delete':
            messages.success(
                request, u'Deleted section: {}'.format(section.title)
            )
            Action.objects.create(
                category='section',
                verb='deleted',
                details=section.title,
                secondary_id=section.book.pk,
            )
            section.delete()
            return redirect('home')

        section_form = SectionForm(
            section.book, request.POST, instance=section, prefix='section'
        )
        author_form = ArtefactAuthorForm(
            request.POST, prefix='author',
        )
        if section_form.is_valid() and author_form.is_valid():
            section = section_form.save(author_form)

            messages.success(
                request, u'Edited section: {}'.format(section.title)
            )

            Action.objects.create(
                primary_id=section.pk,
                verb='edited',
                category='section',
                details=section.title,
                secondary_id=section.book.pk,
            )

            return redirect(section.book)
        else:
            messages.error(request, 'Failed to save section')
    else:
        section_form = SectionForm(
            section.book,
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
    section = get_object_or_404(Section, pk=section_id)

    # Find the previous and next sections (if any) for this book.
    # TODO: Is there a better way to do this? get_next_by is only for DateField

    context = {
        'book': section.book,
        'section': section,
        'previous_section': section.get_previous(),
        'next_section': section.get_next(),
    }

    return render(request, 'view_section.html', context)


# todo: this and author search should be part of a goodreads-connected app which caches intermediate results
def book_search_json(request):
    query = request.GET.get('q')
    results = []

    # Only search goodreads if there's no one with this name in our db
    existing_books = Book.objects.filter(title__icontains=query)
    if existing_books.exists():
        for book in existing_books:
            authors = []
            if book.details:
                for author in book.details.authors.all():
                    authors.append(author.name)

            authors.sort()
            results.append({
                'title': book.title,
                'description': ', '.join(authors),
                'image': '/static/img/bookmarker.png',
                'url': book.get_absolute_url(),
            })
    else:
        # Use the goodreads API
        for book in goodreadstools.get_books_by_title(query):
            description = []
            if book['format']:
                description.append(book['format'])
            if book['publisher']:
                description.append(book['publisher'])
            if book['num_pages']:
                description.append(book['num_pages'])

            title = '{}: {}'.format(book['id'], book['title'])
            authors = ', '.join(a['name']for a in book['authors'])
            results.append({
                'title': title,
                'price': authors,
                'description': ' / '.join(description),
                'image': '/static/img/goodreads.png',
            })

    return JsonResponse({
        'results': results
    })


def author_search_json(request):
    query = request.GET.get('q')
    results = []

    # Put a ! at the end of the query to allow saving. I'm sorry
    should_save = query.endswith('!')
    query = query.strip('!')

    # Only search goodreads if there's no one with this name in our db
    existing_authors = Author.objects.filter(name__icontains=query)
    if existing_authors.exists():
        # todo: urgh
        for author in existing_authors:
            titles = []
            books = set(author.books.values_list('book__title', flat=True))
            for book in books:
                if book:
                    titles.append(book)

            publications = set(author.sections.values_list('book__title', flat=True))
            for publication in publications - books:
                if publication:
                    titles.append(publication)

            titles.sort()
            results.append({
                'title': author.name,
                'description': ', '.join(titles[:10]),
                'image': '/static/img/bookmarker.png',
                'url': author.get_absolute_url(),
            })
    else:
        # Use the goodreads API
        author = goodreadstools.get_author_by_name(query)
        title = '{}: {}'.format(author['id'], author['name'])
        results.append({
            'title': title,
            'description': author['titles'],
            'image': '/static/img/goodreads.png',
        })

    return JsonResponse({
        'results': results
    })


def within_book_search_json(request, book_id):
    """Suggest notes/sections/terms with that keyword"""
    query = request.GET.get('q')
    term = query  # todo: meta options?
    book = Book.objects.get(pk=book_id)

    if len(query) < 3:
        return

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

    return JsonResponse({
        'results': {
            'books': {
                'name': 'Notes',
                'results': results['notes'],
            },
            'authors': {
                'name': 'Terms',
                'results': results['terms'],
            },
            'sections': {
                'name': 'Sections',
                'results': results['sections'],
            },
        }
    })


def search_json(request):
    """Suggest authors/books/sections with that name"""
    query = request.GET.get('q')
    books = []
    authors = []
    sections = []
    if len(query) >= 3:
        for book in Book.objects.filter(title__icontains=query):
            books.append({
                'title': book.title,
                'url': book.get_absolute_url(),
            })
        for author in Author.objects.filter(name__icontains=query):
            authors.append({
                'title': author.name,
                'url': author.get_absolute_url(),
            })
        for section in Section.objects.filter(title__icontains=query):
            sections.append({
                'title': section.title,
                'url': section.get_absolute_url(),
            })

    return JsonResponse({
        'results': {
            'books': {
                'name': 'Books',
                'results': books,
            },
            'authors': {
                'name': 'Authors',
                'results': authors,
            },
            'sections': {
                'name': 'Sections',
                'results': sections,
            },
        }
    })


def search(request):
    query = request.GET.get('q')

    MODES = ('notes', 'terms', 'sections', 'books')
    mode = request.GET.get('mode')
    if mode not in MODES:
        mode = None

    ordering = {
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
        'books': ('title', 'pk'),
    }
    sort = request.GET.get('sort')
    if mode and sort in SORTS[mode]:
        ordering[mode] = sort

    # Split out the meta options. TODO
    term = query

    notes = Note.objects.filter(
        Q(subject__icontains=term) |
        Q(quote__icontains=term) |
        Q(comment__icontains=term)
    )
    terms = TermOccurrence.objects.filter(
        Q(term__text__icontains=term) |
        Q(term__definition__icontains=term) |
        Q(quote__icontains=term) |
        Q(quote__icontains=term)
    )
    sections = Section.objects.filter(
        Q(title__icontains=term) |
        Q(subtitle__icontains=term) |
        Q(summary__icontains=term)
    )
    books = Book.objects.filter(
        Q(title__icontains=term) |
        Q(summary__icontains=term) |
        Q(details__authors__name__icontains=term)
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

    filter_form = SearchFilterForm(request.GET)
    mode_filters = {
        'books': ('author', 'min_rating', 'max_rating'),
        'notes': ('author', 'book' ,'section'),
        'terms': ('author', 'book', 'section', 'category'),
        'sections': ('author', 'book', 'min_rating', 'max_rating'),
    }
    filter_fields = {
        'author': 'authors',
        'book': 'book',
        'section': 'section',
        'category': 'category',
        'min_rating': 'rating__gte',
        'max_rating': 'rating__lte',
    }

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

        author_field_name = 'authors'
        if mode == 'books':
            author_field_name = 'details__authors'
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

        # If sections, show the term/note counts.
        if mode == 'sections':
            results[mode] = results[mode].annotate(
                num_terms=Count('terms', distinct=True),
                num_notes=Count('notes', distinct=True),
            )

        # Apply the filters.
        if filter_form.is_valid():
            filters = {}
            for filter_key in mode_filters[mode]:
                if filter_form.cleaned_data[filter_key]:
                    filter_field = filter_fields[filter_key]
                    filters[filter_field] = filter_form.cleaned_data[filter_key]

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
        results[key] = results[key].order_by(ordering[key]).distinct()

    context = {
        'sort': ordering.get(mode),  # use the implied sort, not the input
        'sort_options': SORTS.get(mode),
        'results': results,
        'query': query,
        'mode': mode,
        'modes': MODES,
        'qs': '?' + urlencode({'q': query}),
        'filter_form': filter_form,
    }

    return render(request, 'search.html', context)


def view_stats(request):
    user = goodreadstools.get_user()
    shelves = user.shelves()
    num_read = shelves[0].count  # assumes that read is first - confirm this
    remaining_shelf = shelves[2]  # assumes that to-read is third - confirm this
    num_remaining = remaining_shelf.count

    # Estimate the end date based on various reading paces.
    pace_per_year = {
        'one_per_month': 12,
        'two_per_month': 24,
        'one_per_week': 52,
        'two_per_week': 104,
        'one_per_day': 365,
    }
    dates = {}
    for pace, count in pace_per_year.items():
        days_left = num_remaining / float(count) * 365
        end_date = datetime.datetime.today() + datetime.timedelta(days=days_left)
        dates[pace] = end_date

    context = {
        'user': user,
        'num_read': num_read,
        'num_remaining': num_remaining,
        'dates': dates,
    }

    return render(request, 'view_stats.html', context)


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, pk=note_id)

    if request.method == 'POST':
        if request.POST.get('submit') == 'delete':
            messages.success(
                request, u'Deleted note: {}'.format(note.subject)
            )
            Action.objects.create(
                category='note',
                verb='deleted',
                details=note.subject,
                secondary_id=note.book.pk,
            )
            note.delete()
            return redirect('home')

        note_form = NoteForm(note.book, request.POST, instance=note, prefix='note')
        author_form = ArtefactAuthorForm(request.POST, prefix='author')
        if note_form.is_valid() and author_form.is_valid():
            note = note_form.save(author_form)
            Action.objects.create(
                primary_id=note.pk,
                verb='edited',
                category='note',
                details=note.subject,
                secondary_id=note.book.pk,
            )
            messages.success(
                request, u'Edited note: {}'.format(note.subject)
            )
            return redirect(note)
        else:
            messages.error(request, 'Failed to save note')
    else:
        note_form = NoteForm(
            note.book,
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

    book = note.book

    context = {
        'note': note,
        'book': book,
        'note_form': note_form,
        'author_form': author_form,
    }

    return render(request, 'edit_note.html', context)


def cite_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)

    notes = tag.notes.prefetch_related(
        'authors', 'section__authors', 'tags', 'book', 'book__details__default_authors',
    ).order_by('book', 'page_number')

    context = {
        'tag': tag,
        'notes': notes,
    }

    return render(request, 'cite_tag.html', context)


def view_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)

    notes = tag.notes.prefetch_related(
        'authors', 'section__authors', 'tags', 'book', 'book__details__default_authors',
    ).order_by('book', 'page_number')
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
    tags = Tag.objects.all().prefetch_related('category').annotate(
        num_notes=Count('notes', distinct=True),
    ).order_by('category__slug', 'slug')

    if not request.user.is_staff:
        tags = tags.filter(hidden=False)

    context = {
        'tags': tags,
    }

    return render(request, 'view_all_tags.html', context)


def view_faves(request):
    strict = bool(request.GET.get('strict'))
    min_rating = 5 if strict else 4

    tags = Tag.objects.filter(faved=True).prefetch_related('notes', 'category')
    fave_sections = Section.objects.filter(rating__gte=min_rating)
    articles = fave_sections.filter(book__details=None).prefetch_related(
        'authors', 'book',
    )
    chapters = fave_sections.exclude(book__details=None).prefetch_related(
        'authors', 'book'
    )
    chapters_books = set(chapters.values_list('book', flat=True))

    # Randomly choose a note from the above tags/articles/chapters.
    note_ids = set(tags.values_list('notes__id', flat=True))
    note_ids |= set(articles.values_list('notes__id', flat=True))
    note_ids |= set(chapters.values_list('notes__id', flat=True))
    random_note = Note.objects.get(pk=random.choice(list(note_ids)))

    # Randomly choose a term occurrence (with a non-empty quote) for a flagged term.
    occurrence_ids = TermOccurrence.objects.filter(
        term__flagged=True,
    ).exclude(
        quote='',
    ).values_list(
        'pk',
        flat=True
    )
    random_vocab = TermOccurrence.objects.get(pk=random.choice(occurrence_ids))

    # Also include any books that are not covered by the sections.
    books = Book.objects.filter(details__rating__gte=min_rating).exclude(id__in=chapters_books).prefetch_related('details')

    context = {
        'strict': strict,
        'random_note': random_note,
        'random_vocab': random_vocab,
        'tags': tags,
        'articles': articles,
        'chapters': chapters,
        'books': books,
    }
    return render(request, 'view_faves.html', context)


@login_required
def add_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            messages.success(request, "Created tag")
            Action.objects.create(
                primary_id=tag.pk,
                category='tag',
                verb='added',
                details=str(tag),
                secondary_id=None,
            )
            return redirect(tag)
        else:
            messages.error(request, "Failed to create tag")
    else:
        form = TagForm()

    context = {
        'form': form,
        'categories': TagCategory.objects.all(),
    }
    return render(request, 'add_tag.html', context)
    

@login_required
def sync_goodreads(request):
    if request.method == 'POST':
        goodreads_id = request.POST.get('id')
        action = request.POST.get('action')
        review = redistools.get_review(goodreads_id)
        
        if review is None:
            messages.error(request, "Invalid goodreads ID")
        else:
            # Delete it so it doesn't show up again.
            redistools.ignore_review(goodreads_id)
            if action == 'ignore':
                messages.success(request, "Successfully ignored {}".format(review['book']['title']))
            else:
                # If there is one existing book, use that one instead.
                existing_books = Book.objects.filter(title=review['book']['title'])
                if existing_books.count() == 1:
                    book = existing_books.first()
                    messages.success(request, 'Updated existing book: {}'.format(book.title))
                else:
                    book = Book.objects.create_from_goodreads(review['book'])
                    messages.success(request, 'Added book: {}'.format(book.title))

                book.details.shelves = review['shelves']
                book.details.review = review['review']
                book.details.rating = review['rating']
                book.details.start_date = parser.parse(
                    review['start_date']
                ).date()
                book.details.end_date = parser.parse(
                    review['end_date']
                ).date()
                book.details.save()

                for author_data in review['book']['authors']:
                    gr_author = GoodreadsAuthor.objects.filter(
                        goodreads_id=author_data['id']
                    )
                    if gr_author.exists():
                        author = gr_author.first().author
                    else:
                        # Author doesn't exist yet - must create.
                        author = Author.objects.create_from_goodreads(author_data)
                        messages.success(request, 'Added author: {}'.format(author.name))

                    book.details.authors.add(author)
                    book.details.default_authors.add(author)

    review = redistools.get_random_review()
    if review:
        # check if we already have a book with this title
        existing_books = Book.objects.filter(
            title=review['book']['title']
        )
    else:
        existing_books = Book.objects.none()

    context = {
        'review': review,
        'existing_books': existing_books,
        'total': redistools.count_reviews(),
    }

    return render(request, 'sync_goodreads.html', context)
