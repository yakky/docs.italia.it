# Base image in the multi stage process - This is not really used by any
# container, it's just a common base

FROM python:3.6-slim AS docs_italia_it_base

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libpq-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && apt-get clean

ENV APPDIR /app
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1 DEBUG=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Test image - Used in `docker-compost-test`.
# As all the test will run in a tox virtualenv we need development libraries here
# We don't need code in this image as will be mounted the live one via the local
# volume

FROM docs_italia_it_base AS docs_italia_it_test

RUN pip install --no-cache-dir tox

CMD ["/bin/bash"]

# Base image for all the application containers (web, api, celery-docs, celery-web)
# We don't need to copy the RTD code in this image as will be mounted the live
# one via the local volume. We only need to copy the files needed inside the
# container (utility shell scripts and requirements)

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
RUN apt-get purge build-essential -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && apt-get clean
ENV DJANGO_SETTINGS_MODULE=readthedocs.docsitalia.settings.docker

CMD ["/bin/bash"]

# Build image for celery-build
# We need additional packages to build documentation in LocalBuildEnvironment


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

RUN apt-get purge build-essential -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && apt-get clean

CMD ["/bin/bash"]

# Production image - To run in production we obviously need to copy the
# application code inside the container

FROM docs_italia_it_web AS docs_italia_it_web_prod

COPY . /app

# Production image - To run in production we obviously need to copy the
# application code inside the container

FROM docs_italia_it_build AS docs_italia_it_build_prod

COPY . /app
