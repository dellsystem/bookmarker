"""bookmarker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin

import bookmarker.views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', bookmarker.views.home, name='home'),
    url(r'^login$', bookmarker.views.LoginView.as_view(), name='login'),
    url(r'^logout$', bookmarker.views.LogoutView.as_view(), name='logout'),
    url(r'^addbook$', bookmarker.views.add_book, name='add_book'),
    url(r'^addbook/id$', bookmarker.views.add_book_from_id, name='add_book_from_id'),
    url(r'^addauthor$', bookmarker.views.add_author, name='add_author'),
    url(r'^addauthor/id$', bookmarker.views.add_author_from_id, name='add_author_from_id'),
    url(r'^books/(?P<book_type>\w+)$', bookmarker.views.view_books, name='view_books'),
    url(r'^authors$', bookmarker.views.view_all_authors, name='view_all_authors'),
    url(r'^terms$', bookmarker.views.view_all_terms, name='view_all_terms'),
    url(r'^notes$', bookmarker.views.view_all_notes, name='view_all_notes'),
    url(r'^s/(?P<slug>[\w-]+)$', bookmarker.views.section_redirect, name='section_redirect'),
    url(r'^book/(?P<slug>[\w-]+)$', bookmarker.views.view_book,
        name='view_book'),
    url(r'^book/(?P<slug>[\w-]+)/edit$', bookmarker.views.edit_book,
        name='edit_book'),
    url(r'^book/(?P<slug>[\w-]+)/addterm$', bookmarker.views.add_term,
        name='add_term'),
    url(r'^book/(?P<slug>[\w-]+)/terms$', bookmarker.views.view_terms,
        name='view_terms'),
    url(r'^book/(?P<slug>[\w-]+)/addnote$', bookmarker.views.add_note,
        name='add_note'),
    url(r'^book/(?P<slug>[\w-]+)/addsection$', bookmarker.views.add_section,
        name='add_section'),
    url(r'^book/(?P<slug>[\w-]+)/addsections$', bookmarker.views.add_sections,
        name='add_sections'),
    url(r'^book/(?P<slug>[\w-]+)/notes$', bookmarker.views.view_notes,
        name='view_notes'),
    url(r'^book/(?P<book_id>\d+)/complete$', bookmarker.views.mark_complete,
        name='mark_complete'),
    url(r'^section/(?P<section_id>\d+)$', bookmarker.views.view_section,
        name='view_section'),
    url(r'^section/(?P<section_id>\d+)/edit$', bookmarker.views.edit_section,
        name='edit_section'),
    url(r'^note/(?P<note_id>\d+)$', bookmarker.views.view_note,
        name='view_note'),
    url(r'^note/(?P<note_id>\d+)/edit$', bookmarker.views.edit_note,
        name='edit_note'),
    url(r'^term/(?P<term_id>\d+)$', bookmarker.views.view_term,
        name='view_term'),
    url(r'^term/(?P<term_id>\d+)/flag$', bookmarker.views.flag_term,
        name='flag_term'),
    url(r'^occurrence/(?P<occurrence_id>\d+)/edit$',
        bookmarker.views.edit_occurrence,
        name='edit_occurrence'),
    url(r'^occurrence/(?P<occurrence_id>\d+)$',
        bookmarker.views.view_occurrence,
        name='view_occurrence'),
    url(r'^author/(?P<slug>[\w-]+)$', bookmarker.views.view_author,
        name='view_author'),
    url(r'^tag/(?P<slug>[^/]+)$', bookmarker.views.view_tag,
        name='view_tag'),
    url(r'^tag/(?P<slug>[^/]+)/cite$', bookmarker.views.cite_tag,
        name='cite_tag'),
    url(r'^tags$', bookmarker.views.view_all_tags, name='view_all_tags'),
    url(r'^tags/add$', bookmarker.views.add_tag, name='add_tag'),
    url(r'^stats$', bookmarker.views.view_stats, name='view_stats'),
    url(r'^api/suggest.json$', bookmarker.views.suggest_terms),
    url(r'^api/define.json$', bookmarker.views.get_definition),
    url(r'^faves$', bookmarker.views.view_faves, name='view_faves'),
    url(r'^search$', bookmarker.views.search, name='search'),
    url(r'^sync$', bookmarker.views.sync_goodreads, name='sync_goodreads'),
    url(r'^search.json$', bookmarker.views.search_json, name='search_json'),
    url(r'^author_search.json$', bookmarker.views.author_search_json, name='author_search_json'),
    url(r'^book_search.json$', bookmarker.views.book_search_json, name='book_search_json'),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
