from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from books.api import CLIENT
from books.forms import NoteForm, SectionForm
from books.models import Book, Author, Note, Section
from vocab.api import lookup_term
from vocab.forms import TermOccurrenceForm
from vocab.models import Term, TermOccurrence


def home(request):
    context = {
        'num_books': Book.objects.count(),
        'num_needing_terms': Book.objects.filter(completed_terms=False).count(),
        'num_needing_notes': Book.objects.filter(completed_notes=False).count(),
        'num_needing_sections': Book.objects.filter(completed_sections=False).count(),
        'books': Book.objects.order_by(
            'completed_notes', 'completed_terms', 'completed_sections', '-pk'
        ),
    }
    return render(request, 'home.html', context)


def view_book(request, book_id):
    book = Book.objects.get(pk=book_id)

    # Divide the sections in half for more compact displaying.
    sections = book.sections.all()
    middle = (sections.count() + 1) / 2
    sections_1 = sections[:middle]
    sections_2 = sections[middle:]

    if book.sections.count() == 0 and book.completed_sections:
        needs_sections = False
    else:
        needs_sections = True

    notes_without_section = book.notes.filter(
        section=None
    ).order_by('section_title')
    terms_without_section = book.terms.filter(
        section=None
    ).order_by('section_title')

    context = {
        'book': book,
        'recent_terms': book.terms.all()[:5],
        'recent_notes': book.notes.all()[:5],
        'sections_1': sections_1,
        'sections_2': sections_2,
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

    new_form = True
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.book = book
            section.save()
            messages.success(request, u'Added section: {}'.format(section.title))
        else:
            new_form = False
            messages.error(request, 'Failed to add section')

    if new_form:
        form = SectionForm()

    # Divide the sections in half for more compact displaying.
    sections = book.sections.all()
    middle = (sections.count() + 1) / 2
    sections_1 = sections[:middle]
    sections_2 = sections[middle:]

    context = {
        'book': book,
        'form': form,
        'sections_1': sections_1,
        'sections_2': sections_2,
    }

    return render(request, 'add_section.html', context)


def add_term(request, book_id):
    book = Book.objects.get(pk=book_id)

    new_form = True
    if request.method == 'POST':
        form = TermOccurrenceForm(request.POST)
        if form.is_valid():
            term, created = Term.objects.get_or_create(
                text=form.cleaned_data['term'],
                language=form.cleaned_data['language'],
                defaults={
                    'definition': form.cleaned_data['definition'],
                    'highlights': form.cleaned_data['term'].lower(),
                },
            )

            # Make sure the section corresponds to the page number, if the
            # book's sections all have page numbers and this page number is
            # numeric.
            try:
                page_number = int(form.cleaned_data['page'])
            except ValueError:
                page_number = None

            # Consider making this a method on some superclass of both Note and
            # TermOccurrence.
            if page_number:
                section_pages = book.get_section_pages()
                for section, first_page in section_pages:
                    if page_number >= first_page:
                        if section == form.cleaned_data['section']:
                            break
                        else:
                            messages.warning(
                                request,
                                'Fixed section (was {was}, now {now})'.format(
                                    was=form.cleaned_data['section'],
                                    now=section,
                                )
                            )
                            form.cleaned_data['section'] = section
                            break

            occurrence = term.occurrences.create(
                book=book,
                section=form.cleaned_data['section'],
                quote=form.cleaned_data['quote'],
                comments=form.cleaned_data['comments'],
                page=form.cleaned_data['page'],
                category=form.cleaned_data['category'],
                is_new=form.cleaned_data['is_new'],
                author=form.cleaned_data['author'],
                is_defined=form.cleaned_data['is_defined'],
            )
            messages.success(request, u'Added term: {}'.format(term.text))
        else:
            new_form = False
            messages.error(request, 'Failed to add term')

    if new_form:
        initial = {
            'language': book.language,
        }

        latest_addition = book.get_latest_addition()
        if latest_addition is not None:
            initial['section'] = latest_addition.section

        # If the book has only one author, set the author to the author of the book
        # by default.
        if book.authors.count() == 1:
            initial['author'] = book.authors.latest('pk')
        elif latest_addition is not None:
            # Otherwise, if this book has multiple authors but we've created
            # a previous TermOccurrence or note, use the author from that.
            initial['author'] = latest_addition.author

        form = TermOccurrenceForm(initial=initial)

    form.fields['section'].queryset = book.sections.all()

    context = {
        'book': book,
        'recent_terms_1': book.terms.all()[:3],
        'recent_terms_2': book.terms.all()[3:6],
        'form': form,
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

    edit_link = None
    if term and language:
        # Check if the term already exists.
        try:
            existing_term = Term.objects.get(text=term, language=language)
        except Term.DoesNotExist:
            existing_term = None

        if existing_term:
            definition = existing_term.definition
            edit_link = reverse('view_term', args=[existing_term.pk])
        else:
            definition = lookup_term(language, term)
    else:
        definition = None

    return JsonResponse({
        'term': term,
        'language': language,
        'definition': definition,
        'edit_link': edit_link,
    })


def add_note(request, book_id):
    book = Book.objects.get(pk=book_id)

    new_form = True
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)

            # Make sure the section corresponds to the page number, if the
            # book's sections all have page numbers and this page number is
            # numeric.
            try:
                page_number = int(note.page)
            except ValueError:
                page_number = None

            # Consider making this a method on some superclass of both Note and
            # TermOccurrence.
            if page_number:
                section_pages = book.get_section_pages()
                for section, first_page in section_pages:
                    if page_number >= first_page:
                        if section == note.section:
                            break
                        else:
                            messages.warning(
                                request,
                                'Fixed section (was {was}, now {now})'.format(
                                    was=note.section,
                                    now=section,
                                )
                            )
                            note.section = section
                            break

            note.book = book
            note.save()
            messages.success(request, u'Added note: {}'.format(note.subject))
        else:
            new_form = False
            messages.error(request, 'Failed to add note')

    if new_form:
        initial = {}

        latest_addition = book.get_latest_addition()
        if latest_addition is not None:
            initial['section'] = latest_addition.section

        # If the book has only one author, set the author to the author of the book
        # by default.
        if book.authors.count() == 1:
            initial['author'] = book.authors.latest('pk')
        elif latest_addition is not None:
            # Otherwise, if this book has multiple authors but we've created
            # a previous note or term, use the author from that.
            initial['author'] = latest_addition.author


        form = NoteForm(initial=initial)

    form.fields['section'].queryset = book.sections.all()

    context = {
        'book': book,
        'form': form,
        'recent_notes_1': book.notes.all()[:3],
        'recent_notes_2': book.notes.all()[3:6],
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
    if mode == 'terms':
        if book.completed_terms:
            messages.error(request, 'Terms already marked as complete')
        else:
            book.completed_terms = True
            book.save()
            messages.success(request, 'Terms marked as complete')
    elif mode == 'notes':
        if book.completed_notes:
            messages.error(request, 'Notes already marked as complete')
        else:
            book.completed_notes = True
            book.save()
            messages.success(request, 'Notes marked as complete')
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


def view_section(request, section_id):
    section = Section.objects.get(pk=section_id)

    context = {
        'book': section.book,
        'section': section,
    }

    return render(request, 'view_section.html', context)
