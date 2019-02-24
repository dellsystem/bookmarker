import datetime
import socket

from fabric.api import *


env.use_ssh_config = True
env.host_string = 'picric'


def re():
    local('sudo systemctl restart bookmarker')


def up():
    local('django/manage.py runserver')

def static():
    local('django/manage.py collectstatic --noinput')


def get_backup_filename(hostname):
    return 'backups/{}_{}.json'.format(
        hostname,
        datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
    )

BACKUP_COMMAND = './django/manage.py dumpdata books vocab activity > '
def backup():
    """Does a local database dump. Returns the filename."""
    local_filename = get_backup_filename(hostname=socket.gethostname())
    local(BACKUP_COMMAND + local_filename)

    return local_filename


def backup_remote():
    """Does a remote database dump and scps the file. Returns the filename."""
    remote_filename = get_backup_filename(hostname=env.host_string)
    print("Remote filename: " + remote_filename)

    with cd('bookmarker'):
        run('source env/bin/activate && ' + BACKUP_COMMAND + remote_filename)
        # scp the remote backup file to local.
        get(remote_filename, remote_filename)

    return remote_filename


def confirm_local():
    if socket.gethostname() == env.host_string:
        abort("You're on the remote machine (run this locally)")


# ONLY RUN THIS LOCALLY. Exports the local database dump.
def exp():
    confirm_local()

    # First, backup remotely & download the file.
    backup_remote()

    # Then backup locally.
    local_filename = backup()

    # Move the local dump over to remote.
    put(local_filename, 'bookmarker/backups')

    with cd('bookmarker'):
        # Then run loaddata.
        run('source env/bin/activate && django/manage.py loaddata ' + local_filename)
