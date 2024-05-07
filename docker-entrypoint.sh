#!/bin/sh

echo "Create database migrations"
python manage.py makemigrations

echo "Apply database migrations"
python manage.py migrate

gunicorn --bind 0.0.0.0:8000 main.wsgi