NOW=$(date +"%m-%d-%Y")
python manage.py dumpdata --indent=4 books > "backups/books_$NOW.json"
python manage.py dumpdata --indent=4 vocab > "backups/vocab_$NOW.json"
