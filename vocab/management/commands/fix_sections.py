from django.core.management.base import NoArgsCommand
from vocab.models import TermOccurrence
from books.models import Book, Note


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        for book in Book.objects.all():
            has_pages = (
                book.sections.count() > 0 and
                book.sections.filter(first_page='').count() == 0
            )
            page_sections = []
            for section in book.sections.all():
                try:
                    page_number = int(section.first_page)
                except ValueError:
                    continue

                page_sections.append((page_number, section))

            print book.title, "/", book.authors.all(), "========="

            if page_sections:
                page_sections.reverse()

                for t in book.terms.filter(section=None):
                    try:
                        page_number = int(t.page)
                    except ValueError:
                        continue

                    for first_page, section in page_sections:
                        if page_number >= first_page:
                            print "Setting", page_number, "to", section, first_page
                            t.section = section
                            t.save()
                            break

                for n in book.notes.filter(section=None):
                    try:
                        page_number = int(n.page)
                    except ValueError:
                        continue

                    for first_page, section in page_sections:
                        if page_number >= first_page:
                            print "Setting", page_number, "to", section, first_page
                            n.section = section
                            n.save()
                            break
            else:
                # See if we can assign any based on section title.
                for t in book.terms.filter(section=None):
                    sections = book.sections.filter(title__iexact=t.section_title.lower())
                    if sections.exists():
                        t.section = sections.first()
                        t.save()
                        print "Setting", t.section_title

                for n in book.notes.filter(section=None):
                    sections = book.sections.filter(title__iexact=n.section_title.lower())
                    if sections.exists():
                        n.section = sections.first()
                        n.save()
                        print "Setting", n.section_title
