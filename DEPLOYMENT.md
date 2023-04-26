# Deployment instructions

This document is only for me, Wendy. My goal is to document how I deployed
this horrific app because I know I will forget something important at a
crucial juncture. You do not need to read this if you're merely curious about
how this app works. Please do not read this.

_New deployment as of April 26, 2023_

Source material:

* https://daveceddia.com/deploy-git-repo-to-server/
* https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04#creating-the-postgresql-database-and-user

## Server details

Running on a $12/month Digital Ocean droplet named 'bookmarker'. 2GB RAM,
50GB disk. Probably overkill.

Logging in as root. Using .ssh/config to simplify (IP address).

### Nginx

conf file in /etc/nginx/sites-enabled/bookmarker [soft linked from
sites-available]

```
server {
        listen 80;
        server_name bookmarker.dellsystem.me;

        location = /favicon.ico {
                access_log off;
                log_not_found off;
        }

        location /static/ {
                root /var/www/bookmarker;
        }

        location / {
                include proxy_params;
                proxy_pass http://unix:/run/gunicorn.sock;
        }
}
```

To reload:

```
nginx -t && systemctl restart nginx
```

### Gunicorn

Conf file in /etc/systemd/system/gunicorn.service:

```
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/bookmarker/src
EnvironmentFile=/root/bookmarker/env/bin/variables
ExecStart=/root/bookmarker/env/bin/gunicorn \
        --access-logfile - \
        --workers 3 \
        --bind unix:/run/gunicorn.sock \
        bookmarker.wsgi:application

[Install]
WantedBy=multi-user.target
```

Restart with

```
systemctl restart gunicorn
```

### Django settings

I added the following files to env/bin/activate:

```
. variables
export POSTGRES_PASSWORD
export DJANGO_SECRET_KEY
```

and then env/bin/variables looks like this:

```
POSTGRES_PASSWORD='omitted'
DJANGO_SECRET_KEY='omitted'
```

### Postgres

Followed the directions in the tutorial. Database and user both named
bookmarker.

## Backup procedure

Every three days, a gzipped JSON file gets uploaded to Digital Ocean spaces.

I created the file /root/bookmarker/env/bin/django-backup-to-spaces (chmod +x)
```
# First, dump the data to a compressed JSON file.
date_stamp=`date +\%y-\%m-\%d`
filename="/root/bookmarker/backups/bookmarker_${date_stamp}.json.gz"
/var/www/bookmarker/src/manage.py dumpdata books vocab activity -o $filename
# Then use rclone to transfer it to digital ocean spaces
rclone copy $filename digitalocean:dellsystem-backups/bookmarker/database
```

Then I set up the rclone config file, located at ~/.config/rclone/rclone.conf:

```
[digitalocean]
type = s3
env_auth = false
access_key_id = [omitted]
secret_access_key = [omitted]
region =
endpoint = sfo2.digitaloceanspaces.com
location_constraint =
acl =
server_side_encryption =
storage_class =
```

Then I edited the crontab to say:
```
0 0 */3 * * . /root/bookmarker/env/bin/activate && /root/bookmarker/env/bin/django-backup-to-spaces
```

### Troubleshooting

I installed postfix [local] for debugging cronjob errors:

```
tail -f /var/mail/root
```

## Deploying from git

Using a bare git repo, located at `/root/bookmarker/bare_repo.git`.

To deploy, make sure there is a remote for the repository on your local machine
named like prod or something. The URL should be:
`bm:/root/bookmarker/bare_repo.git`

Then, to deploy, do `git push master prod`. You may have to restart gunicorn
and possibly re-collect static files.

If migrations need to be applied, run makemigrations then migrate.

### Post-receive hook

The post-receive hook in the bare repo looks like this

```
#!/bin/sh

# Check out the files
git --work-tree=/var/www/bookmarker --git-dir=/root/bookmarker/bare_repo.git checkout -f
```

### Updating static files

```
/var/www/bookmarker/src/manage.py collectstatic --noinput
```
