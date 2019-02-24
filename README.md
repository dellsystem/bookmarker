![Bookmarker](https://raw.githubusercontent.com/dellsystem/bookmarker/master/django/static/bookmarker.png)

A personal project to help me retain information from the books I'm reading. 

Currently only supports a single user, but I plan to extend it to support
multiple users eventually.

Demo
----

You can view a read-only active demo at <http://bookmarker.dellsystem.me>. This
is also a great way to creep on what books I'm reading.

Setup
-----

Django 1.10. Run `python django/manage.py runserver`.

(Optional) set the following environment variables (ideally using virtualenv)

* `DJANGO_SECRET_KEY`
* `POSTGRES_PASSWORD`
* `GOODREADS_KEY` and `GOODREADS_SECRET` for using the [Goodreads API](https://www.goodreads.com/api/keys)

License
-------

MIT

Contact
-------

If this is something you'd be interested in using, send me an email at
ilostwaldo@gmail.com.
