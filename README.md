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
with Django 3.11. Pip requirements can be found in requirements.txt.

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

### Setting up the Goodreads integration

For the moment, this app currently makes heavy use of the Goodreads API when
adding books and authors. You'll need to get a Goodreads account, and then
you'll have to set up a developer key to access the Goodreads API. This part
is a little annoying, but I haven't figured out how to skip it yet, so in the
meantime you'll need to do this or Bookmarker won't run.

Using your browser, navigate to <https://www.goodreads.com/api/keys>, fill in
the form (the details don't really matter - call it whatever you want, and
leave the optional fields blank) and click "Apply for a Developer Key". Now,
at the top of the page it should say something like

```
key: KEY
secret: SECRET
```

We'll have to save both the key and the secret to our virtualenv. Open up
env/bin/activate (it's a text file), and add this to the end of the file (replace
KEY and SECRET with their respective values):

```
GOODREADS_KEY='KEY'
export GOODREADS_KEY
GOODREADS_SECRET='SECRET'
export GOODREADS_SECRET
```

For that to take effect, you'll have to exit the virtualenv then activate it
again. Run:

```
deactivate && source env/bin/activate
```

You'll also need to authorize the app to use your account. This is even more
annoying and I will try to find a way to make this step optional, but again,
for now it's mandatory. In the bookmarker directory, open up a Python shell
(run `python`) and paste in the following:

```python
import os
from goodreads import client

CLIENT = client.GoodreadsClient(
    os.environ.get('GOODREADS_KEY'),
    os.environ.get('GOODREADS_SECRET'),
)

CLIENT.authenticate()

```

This _should_ pop up a window in your browser (if it doesn't, copy and paste
the URL shown). Authorize the app in your browser, then return to your Python
shell, and type 'y' in response to the prompt ("Have you authorized me?").

Now you'll be able to get your token and secret. In your Python shell, type

```python
CLIENT.session.access_token, CLIENT.session.access_token_secret
```

This will output two strings in a tuple, looking something like this:

```python
('24o7htksgslilu5l3w5h', 'slektlyl3wy5wl3y53wskhgksdhgkldshgsdlg')
```

Open up env/bin/activate one last time and add those to the bottom:

```
GOODREADS_ACCESS_TOKEN='24o7htksgslilu5l3w5h'
export GOODREADS_ACCESS_TOKEN
GOODREADS_ACCESS_SECRET='slektlyl3wy5wl3y53wskhgksdhgkldshgsdlg'
export GOODREADS_ACCESS_SECRET
```

(replacing the token and secret above with whatever was output in your shell)

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

To confirm that the Goodreads API integration worked, visit
<http://localhost:8000/stats> (or click "Stats" in the top menu). It should
display your Goodreads profile picture as well as the number of books you have
on your "read" and "to-read" shelves.

## Adding data

To add a book, navigate to the book's page on Goodreads, then get the book's
Goodreads ID from the URL. For example, if the URL is

```
https://www.goodreads.com/book/show/369873.A_Hacker_Manifesto
```

then the Goodreads ID is 369873. From the dashboard, paste that into the "Book"
field in the top right, then press + or hit enter. You'll now be able to add
chapters to the book if you like (optional). Click the green arrow button when
done, and you'll be presented with the option to add notes (for quotes) and
terms (for vocabulary). If the book details didn't quite get saved properly,
click the edit icon next to the book title.

**NEW**: You can now add books via the "b b" keyboard shortcut. This is
recommended over the copy-and-paste the ID method above. To add an author, use
"a a".

To add an author, find the Goodreads ID for the author (same method), and use
the Author field from the dashboard or the author page. If the author doesn't
have a Goodreads page, just click the + button directly to add the author
details manually. The rest should be fairly self-explanatory, though I make no
guarantees when it comes to usability.

If anything is confusing or buggy, feel free to contact me.

## Advanced

If you want to deploy this in production, I'd recommend using nginx, gunicorn,
systemd, and postgres. To enable postgres, set POSTGRES_PASSWORD.

Unit tests (the few that exist) can be run with `python src/manage.py test`.

## Contact

If this is something you'd be interested in using, send me an email at
ilostwaldo@gmail.com.
