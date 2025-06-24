FROM python:3.11.1

LABEL name="Nova Discord Bot"
LABEL author="Rin"
LABEL version="0.1.0"

ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=settings

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app
COPY nova/scripts/django-entrypoint.sh /app/scripts/django-entrypoint.sh

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p \
    /var/lib/nova/logs/history \
    /var/lib/nova/logs/tracebacks \
    /var/lib/nova/logs/lavalink \
    /var/lib/nova/cache

RUN chmod -R 777 /var/lib/nova
RUN chmod +x /app/scripts/django-entrypoint.sh

CMD ["/app/scripts/django-entrypoint.sh"]