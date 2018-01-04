import datetime

from fabric.api import *


env.use_ssh_config = True
env.host_string = 'stratus'


def up():
    local('django/manage.py runserver')

def static():
    local('django/manage.py collectstatic --noinput')


def get_backup_filename(hostname):
    return 'backups/{}_{}.json'.format(
        hostname,
        datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
    )

BACKUP_COMMAND = 'python manage.py dumpdata books vocab > '
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
        run(BACKUP_COMMAND + remote_filename)
        # scp the remote backup file to local.
        get(remote_filename, remote_filename)

    return remote_filename
