![Bookmarker](https://raw.githubusercontent.com/dellsystem/bookmarker/master/src/static/bookmarker.png)

A personal project to help me retain information from the books I'm reading.
MIT license.

Currently only supports a single user, but I plan to extend it to support
multiple users eventually.

## Demo

You can view a read-only active demo at <http://bookmarker.dellsystem.me>. This
is also a great way to creep on what books I'm reading.

## Setup

If you're familiar with Django, you can skip this; it's a standard deployment
with Django 4.1. Pip requirements can be found in requirements.txt.

Here's the step-by-step for how to set it up via the command line on a Linux
machine that already has git, Python (v3), and virtualenv installed:

### Cloning from git

This will create a folder called "bookmarker" in your working directory with
all the necessary code.

If you have a Github account with your SSH keys set up:
```
git clone git@github.com:dellsystem/bookmarker.git
```
Otherwise:
```
git clone https://github.com/dellsystem/bookmarker.git
```

### Setting up the virtualenv

Now, access the new directory (`cd bookmarker`). You'll want to set up a
virtualenv in this directory for installing all the dependencies (basically a
way to isolate requirements so you can develop multiple projects on the same
machine). The exact command may depend on your setup, but for me, it looks like
this:

```
virtualenv -p python3 env
```

This creates a new directory named "env" within "bookmarker", which will
contain all the Python dependencies for this project. You'll want to activate
the virtualenv every time you need to run Bookmarker, which you can do in the
command line by running

```
source env/bin/activate
```

I personally set up an alias to do this automatically every time I need to
work on a project. In my bash profile, I have aliases like

```
alias bm="cd ~/Projects/bookmarker && source env/bin/activate"
```

so I can just type "bm" in a terminal any time I need to work on Bookmarker.

You can leave the virtualenv at any time with the command `deactivate`.

### Installing the dependencies

Now that you're in the virtualenv, it's to install all the dependencies. This
might be a little finnicky depending on your machine and on the state of the
dependencies at any given time - if you run into any problems, I'd suggest
either Googling the error messages or deleting dependencies from
requirements.txt until you get it working (some of them don't need to be there
explicitly).

```
pip install -r requirements.txt
```

(Make sure you're in the project directory - mine is ~/Projects/bookmarker.)

### Setting up the database

For development, we use SQLite, which you may have to install through your OS
package manager. In production, you should PostgreSQL or something like that
(if that's running locally, all you have to do is set up `POSTGRES_PASSWORD` as
an environment variable), but don't worry about that for now.

To set up the database initially (and create all the basic tables), run:

```
python src/manage.py makemigrations activity books vocab
python src/manage.py migrate
```

(Again, this should be in the project directory, bookmarker/).

This will create all the database tables needed for this app to work.

### Setting up your account

You'll want to create an admin account to access the admin tools &
add/edit/delete data via the frontend. Run

```
python src/manage.py createsuperuser
```

and set your desired username/password. Don't worry about the email address.


Almost done, I promise! Final step: reactivate the virtualenv one more time.

```
deactivate && source env/bin/activate
```

### Running your server locally

Now you're all set to test it out! Run

```
python src/manage.py runserver
```

and navigate your browser to http://localhost:8000. It should show you an empty
dashboard. To log in, click the "Log in" link in the menu and enter the
username and password you set earlier.

## Adding data

TODO [goodreads sync page]

note: it's currently hardcoded to my user id lol

## Advanced

If you want to deploy this in production, I'd recommend using nginx, gunicorn,
systemd, and postgres. To enable postgres, set `POSTGRES_PASSWORD`.

Unit tests (the few that exist) can be run with `python src/manage.py test`.

## Contact

If this is something you'd be interested in using, send me an email at
ilostwaldo@gmail.com.
