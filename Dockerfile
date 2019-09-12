# Base

FROM python:3.6-slim AS docs_italia_it_base

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libpq-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

ENV APPDIR /app
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1 DEBUG=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Test

FROM docs_italia_it_base AS docs_italia_it_test

RUN pip install --no-cache-dir tox

CMD ["/bin/bash"]

# Web

FROM docs_italia_it_base AS docs_italia_it_web

RUN apt-get update && apt-get install -y --no-install-recommends \
        libfreetype6-dev \
        libjpeg-dev \
        libjpeg-turbo-progs \
        libtiff5-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -mvenv /virtualenv
COPY requirements/* /app/
COPY docker /app
RUN /virtualenv/bin/pip install -r /app/docsitalia.txt
RUN apt purge -y build-essential && apt autoremove -y && apt clean
ENV DJANGO_SETTINGS_MODULE=readthedocs.docsitalia.settings.docker

CMD ["/bin/bash"]

# Build

FROM docs_italia_it_web AS docs_italia_it_build

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        doxygen \
        libcairo2-dev \
        libenchant1c2a \
        libevent-dev \
        libgraphviz-dev \
        liblcms2-dev \
        libwebp-dev \
        pandoc \
        pkg-config \
        python-m2crypto \
        python-matplotlib \
        python-pip \
        python-virtualenv \
        python2.7 \
        python2.7-dev \
        sqlite \
        texlive-extra-utils \
        texlive-fonts-recommended \
        texlive-generic-recommended \
        texlive-latex-extra \
        texlive-latex-recommended \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]

# Web Prod

FROM docs_italia_it_web AS docs_italia_it_web_prod

COPY . /app

# Build Prod

FROM docs_italia_it_build AS docs_italia_it_build_prod

COPY . /app
