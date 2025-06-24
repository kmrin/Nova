#!/bin/bash

set -e

handle_term() {
    echo "Received SIGTERM/SIGINT, shutting down..."

    if [ -n "$django_pid" ]; then
        kill -TERM "$django_pid"
        wait "$django_pid"
    fi

    exit 0
}

trap handle_term SIGTERM SIGINT

python manage.py makemigrations
python manage.py migrate

if [ "$BOT_RUN_WITH_DJANGO" = "True" ]; then
    echo "Starting Django with bot integration..."
    python manage.py runserver --noreload 0.0.0.0:8000 &
else
    echo "Starting Django without bot integration..."
    python manage.py runserver 0.0.0.0:8000 &
fi

django_pid=$!

wait $django_pid 