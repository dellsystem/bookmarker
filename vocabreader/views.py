from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from books.api import CLIENT
from books.forms import NoteForm, SectionForm, ArtefactAuthorForm
from books.models import Book, Author, Note, Section
from vocab.api import lookup_term
from vocab.forms import TermForm, TermOccurrenceForm
from vocab.models import Term, TermOccurrence


def home(request):
    books = Book.objects.all().order_by(
        'is_processed', 'completed_sections', '-pk'
    )

    context = {
        'started_books': books.filter(
            is_processed=False,
            completed_sections=True
        ),
        'new_books': books.filter(
            is_processed=False,
            completed_sections=False
        ),
        'done_books': books.filter(is_processed=True),
    }
    return render(request, 'home.html', context)


def view_book(request, book_id):
    book = Book.objects.get(pk=book_id)

    if book.sections.count() == 0 and book.completed_sections:
        needs_sections = False
    else:
        needs_sections = True

    notes_without_section = book.notes.filter(section=None)
    terms_without_section = book.terms.filter(section=None)

    context = {
        'book': book,
        'recent_terms': book.terms.order_by('-added')[:5],
        'recent_notes': book.notes.order_by('-added')[:5],
        'notes_without_section': notes_without_section,
        'terms_without_section': terms_without_section,
        'needs_sections': needs_sections,
    }
    return render(request, 'view_book.html', context)


def view_terms(request, book_id):
    book = Book.objects.get(pk=book_id)
    terms = book.terms.all()
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
    }
    return render(request, 'view_terms.html', context)


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
            section = section_form.save(book=book)

            # Set the authors according to author_form. If the mode is 'none',
            # we don't need to do anything since the section has no authors
            # by default.
            author_mode = author_form.cleaned_data['mode']
            if author_mode == 'default':
                section.authors.add(*book.default_authors.all())
            elif author_mode == 'custom':
                section.authors.add(author_form.cleaned_data['author'])

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


def add_term(request, book_id):
    book = Book.objects.get(pk=book_id)

    if not book.completed_sections:
        messages.error(request, 'Sections need to be completed first')
        return redirect(book)

    new_forms = True
    if request.method == 'POST':
        term_form = TermForm(request.POST, prefix='term')
        occurrence_form = TermOccurrenceForm(request.POST, prefix='occurrence')
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

            occurrence = occurrence_form.save(term=term, book=book)

            # Set the authors according to author_form. If the mode is 'none',
            # we don't need to do anything since the occurrence has no authors
            # by default.
            author_mode = author_form.cleaned_data['mode']
            if author_mode == 'default':
                occurrence.set_default_authors()
            elif author_mode == 'custom':
                occurrence.authors.add(author_form.cleaned_data['author'])

            messages.success(request, u'Added term: {}'.format(term.text))
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
            if Author.objects.filter(goodreads_id=gr_author.gid).exists():
                book.authors.add(Author.objects.get(goodreads_id=gr_author.gid))
                continue

            author = book.authors.create(
                goodreads_id=gr_author.gid,
                name=gr_author.name,
                link=gr_author.link,
            )
            messages.success(
                request,
                u'Added author: {}'.format(author.name),
            )

    return redirect(book)


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
            highlights = term.lower()

    return JsonResponse({
        'term': term,
        'language': language,
        'definition': definition,
        'highlights': highlights,
        'view_link': view_link,
        'num_occurrences': num_occurrences,
    })


def add_note(request, book_id):
    book = Book.objects.get(pk=book_id)

    if not book.completed_sections:
        messages.error(request, 'Sections need to be completed first')
        return redirect(book)

    new_form = True
    if request.method == 'POST':
        note_form = NoteForm(request.POST, prefix='note')
        author_form = ArtefactAuthorForm(request.POST, prefix='author')

        if note_form.is_valid() and author_form.is_valid():
            note = note_form.save(book=book)

            # Set the authors according to author_form. If the mode is 'none',
            # we don't need to do anything since the occurrence has no authors
            # by default.
            author_mode = author_form.cleaned_data['mode']
            if author_mode == 'default':
                note.set_default_authors()
            elif author_mode == 'custom':
                note.authors.add(author_form.cleaned_data['author'])

            messages.success(request, u'Added note: {}'.format(note.subject))
        else:
            new_form = False
            messages.error(request, 'Failed to add note')

    if new_form:
        note_form = NoteForm(prefix='note')
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


def view_notes(request, book_id):
    book = Book.objects.get(pk=book_id)
    notes = book.notes.all()
    paginator = Paginator(notes, 5)

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
    }

    return render(request, 'view_notes.html', context)


def view_note(request, note_id):
    note = Note.objects.get(pk=note_id)

    context = {
        'book': note.book,
        'note': note,
    }

    return render(request, 'view_note.html', context)


def view_term(request, term_id):
    term = Term.objects.get(pk=term_id)
    context = {
        'term': term,
        'occurrences': term.occurrences.all(),
    }
    return render(request, 'view_term.html', context)


def view_author(request, author_id):
    author = Author.objects.get(pk=author_id)
    context = {
        'author': author,
    }
    return render(request, 'view_author.html', context)


def view_all_terms(request):
    terms = TermOccurrence.objects.order_by('term')
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
        'terms': terms,
    }

    return render(request, 'view_all_terms.html', context)


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


def edit_section(request, section_id):
    section = Section.objects.get(pk=section_id)

    initial_author = None
    if section.authors.count():
        if section.has_default_authors():
            author_mode = 'default'
        else:
            author_mode = 'custom'
            initial_author = section.authors.first()
    else:
        author_mode = 'none'

    if request.method == 'POST':
        section_form = SectionForm(
            request.POST, instance=section, prefix='section'
        )
        author_form = ArtefactAuthorForm(
            request.POST, prefix='author',
        )
        if section_form.is_valid() and author_form.is_valid():
            section = section_form.save()

            # Set the authors according to author_form (only if the mode has
            # changed).
            new_author_mode = author_form.cleaned_data['mode']
            if author_mode != new_author_mode:
                if new_author_mode == 'default':
                    section.set_default_authors()
                else:
                    # If it's "none", we only need to remove authors.
                    section.authors.clear()
                    if new_author_mode == 'custom':
                        section.authors.add(author_form.cleaned_data['author'])

            messages.success(
                request, u'Edited section: {}'.format(section.title)
            )
            return redirect(section.book)

    section_form = SectionForm(instance=section, prefix='section')

    author_form = ArtefactAuthorForm(
        prefix='author',
        initial={
        'mode': author_mode,
        'author': initial_author,
        }
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
    next_section = None
    previous_section = None
    book_sections = section.book.sections.all()
    num_sections = len(book_sections)
    for i, book_section in enumerate(book_sections):
        if book_section.pk == section.pk:
            if i < num_sections - 1:
                next_section = book_sections[i + 1]
            if i > 0:
                previous_section = book_sections[i - 1]
            break

    context = {
        'book': section.book,
        'section': section,
        'previous_section': previous_section,
        'next_section': next_section,
    }

    return render(request, 'view_section.html', context)
