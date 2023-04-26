"""bookmarker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import path, re_path, include
from django.contrib import admin

import bookmarker.views


urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', bookmarker.views.home, name='home'),
    path('login', bookmarker.views.LoginView.as_view(), name='login'),
    re_path(r'^logout$', bookmarker.views.LogoutView.as_view(), name='logout'),
    re_path(r'^addbook$', bookmarker.views.add_book, name='add_book'),
    re_path(r'^addauthor$', bookmarker.views.add_author, name='add_author'),
    re_path(r'^books/(?P<book_type>\w+)$', bookmarker.views.view_books, name='view_books'),
    re_path(r'^authors$', bookmarker.views.view_all_authors, name='view_all_authors'),
    re_path(r'^terms$', bookmarker.views.view_all_terms, name='view_all_terms'),
    re_path(r'^notes$', bookmarker.views.view_all_notes, name='view_all_notes'),
    re_path(r'^print/tag/(?P<slug>[\w-]+)$', bookmarker.views.print_tag, name='print_tag'),
    re_path(r'^s/(?P<slug>[\w-]+)$', bookmarker.views.section_redirect, name='section_redirect'),
    re_path(r'^book/(?P<slug>[\w-]+)$', bookmarker.views.view_book,
        name='view_book'),
    re_path(r'^book/(?P<slug>[\w-]+)/edit$', bookmarker.views.edit_book,
        name='edit_book'),
    re_path(r'^book/(?P<slug>[\w-]+)/addterm$', bookmarker.views.add_term,
        name='add_term'),
    re_path(r'^book/(?P<slug>[\w-]+)/terms$', bookmarker.views.view_terms,
        name='view_terms'),
    re_path(r'^book/(?P<slug>[\w-]+)/addnote$', bookmarker.views.add_note,
        name='add_note'),
    re_path(r'^book/(?P<slug>[\w-]+)/addsection$', bookmarker.views.add_section,
        name='add_section'),
    re_path(r'^book/(?P<slug>[\w-]+)/addsections$', bookmarker.views.add_sections,
        name='add_sections'),
    re_path(r'^book/(?P<slug>[\w-]+)/notes$', bookmarker.views.view_notes,
        name='view_notes'),
    re_path(r'^book/(?P<book_id>\d+)/complete$', bookmarker.views.mark_complete,
        name='mark_complete'),
    re_path(r'^book/(?P<book_id>\d+)/search.json$', bookmarker.views.within_book_search_json,
        name='within_book_search_json'),
    re_path(r'^section/(?P<section_id>\d+)$', bookmarker.views.view_section,
        name='view_section'),
    re_path(r'^section/(?P<section_id>\d+)/edit$', bookmarker.views.edit_section,
        name='edit_section'),
    re_path(r'^note/(?P<note_id>\d+)$', bookmarker.views.view_note,
        name='view_note'),
    re_path(r'^note/(?P<note_id>\d+)/edit$', bookmarker.views.edit_note,
        name='edit_note'),
    re_path(r'^term/(?P<term_id>\d+)$', bookmarker.views.view_term,
        name='view_term'),
    re_path(r'^term/(?P<term_id>\d+)/flag$', bookmarker.views.flag_term,
        name='flag_term'),
    re_path(r'^occurrence/(?P<occurrence_id>\d+)/edit$',
        bookmarker.views.edit_occurrence,
        name='edit_occurrence'),
    re_path(r'^occurrence/(?P<occurrence_id>\d+)$',
        bookmarker.views.view_occurrence,
        name='view_occurrence'),
    re_path(r'^author/(?P<slug>[\w-]+)$', bookmarker.views.view_author,
        name='view_author'),
    re_path(r'^tag/(?P<slug>[^/]+)$', bookmarker.views.view_tag,
        name='view_tag'),
    re_path(r'^tag/(?P<slug>[^/]+)/cite$', bookmarker.views.cite_tag,
        name='cite_tag'),
    re_path(r'^tags$', bookmarker.views.view_all_tags, name='view_all_tags'),
    re_path(r'^tags/add$', bookmarker.views.add_tag, name='add_tag'),
    re_path(r'^stats$', bookmarker.views.view_stats, name='view_stats'),
    re_path(r'^api/suggest.json$', bookmarker.views.suggest_terms),
    re_path(r'^api/define.json$', bookmarker.views.get_definition),
    re_path(r'^faves$', bookmarker.views.view_faves, name='view_faves'),
    re_path(r'^search$', bookmarker.views.search, name='search'),
    re_path(r'^sync$', bookmarker.views.sync_goodreads, name='sync_goodreads'),
    re_path(r'^search.json$', bookmarker.views.search_json, name='search_json'),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
