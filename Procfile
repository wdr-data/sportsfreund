web: PYTHONPATH=${PYTHONPATH}:./ gunicorn --chdir app main.wsgi --log-file -
release: python app/manage.py migrate
worker: cd worker && mrq-worker
