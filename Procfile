web: gunicorn --chdir back back.wsgi
worker: celery --workdir=back -A back worker --beat -l info