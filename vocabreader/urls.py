"""vocabreader URL Configuration

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
from django.conf.urls import url
from django.contrib import admin

import vocabreader.views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', vocabreader.views.home, name='home'),
    url(r'^addbook$', vocabreader.views.add_book, name='add_book'),
    url(r'^terms$', vocabreader.views.view_all_terms, name='view_all_terms'),
    url(r'^book/(?P<book_id>\d+)$', vocabreader.views.view_book,
        name='view_book'),
    url(r'^book/(?P<book_id>\d+)/addterm$', vocabreader.views.add_term,
        name='add_term'),
    url(r'^book/(?P<book_id>\d+)/viewterms$', vocabreader.views.view_terms,
        name='view_terms'),
    url(r'^book/(?P<book_id>\d+)/addnote$', vocabreader.views.add_note,
        name='add_note'),
    url(r'^book/(?P<book_id>\d+)/addsection$', vocabreader.views.add_section,
        name='add_section'),
    url(r'^book/(?P<book_id>\d+)/viewnotes$', vocabreader.views.view_notes,
        name='view_notes'),
    url(r'^book/(?P<book_id>\d+)/complete$', vocabreader.views.mark_complete,
        name='mark_complete'),
    url(r'^section/(?P<section_id>\d+)$', vocabreader.views.view_section,
        name='view_section'),
    url(r'^section/(?P<section_id>\d+)/edit$', vocabreader.views.edit_section,
        name='edit_section'),
    url(r'^note/(?P<note_id>\d+)$', vocabreader.views.view_note,
        name='view_note'),
    url(r'^term/(?P<term_id>\d+)$', vocabreader.views.view_term,
        name='view_term'),
    url(r'^author/(?P<author_id>\d+)$', vocabreader.views.view_author,
        name='view_author'),
    url(r'^api/define.json$', vocabreader.views.get_definition),
]
