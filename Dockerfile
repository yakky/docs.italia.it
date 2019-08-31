FROM python:3.6-slim

ENV DEBIAN_FRONTEND noninteractive

RUN python -mvenv /virtualenv

RUN apt update && apt dist-upgrade -y

RUN apt install --no-install-recommends -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libpq-dev \
    libtiff5-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libjpeg-turbo-progs \
    libffi-dev \
    git

COPY requirements/* /app/

RUN /virtualenv/bin/pip install -r /app/docsitalia.txt

COPY . /app

ENV APPDIR /app
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=readthedocs.docsitalia.settings.docker
ENV DEBUG=1
WORKDIR /app
RUN chmod +x docker/*sh
