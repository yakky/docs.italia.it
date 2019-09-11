FROM python:3.6-slim AS docs_italia_it_base

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt install --no-install-recommends -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libpq-dev \
    git && rm -rf /var/lib/apt/lists/* && apt clean

ENV APPDIR /app
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1 DEBUG=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

FROM docs_italia_it_base AS docs_italia_it_test

RUN pip install tox

CMD ["/bin/bash"]

FROM docs_italia_it_base AS docs_italia_it_web

RUN apt update && apt install --no-install-recommends -y \
    libtiff5-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libjpeg-turbo-progs \
    && rm -rf /var/lib/apt/lists/*

RUN python -mvenv /virtualenv
COPY requirements/* /app/
COPY docker /app
RUN /virtualenv/bin/pip install -r /app/docsitalia.txt
RUN apt purge -y build-essential && apt autoremove -y && apt clean
ENV DJANGO_SETTINGS_MODULE=readthedocs.docsitalia.settings.docker

CMD ["/bin/bash"]

FROM docs_italia_it_web AS docs_italia_it_build

RUN apt update && apt install --no-install-recommends -y \
    python2.7 \
    python2.7-dev \
    python-pip \
    python-virtualenv \
    texlive-generic-recommended \
    texlive-latex-recommended \
    texlive-extra-utils \
    libfreetype6 g++ sqlite libevent-dev libffi-dev \
    libenchant1c2a curl python-m2crypto python-matplotlib \
    libgraphviz-dev pandoc doxygen python3 python3-dev python3-pip \
    texlive-latex-extra pkg-config libjpeg-dev \
    libfreetype6-dev libtiff5-dev zlib1g-dev liblcms2-dev \
    libwebp-dev libcairo2-dev texlive-fonts-recommended

RUN apt autoremove -y && apt clean

CMD ["/bin/bash"]

FROM docs_italia_it_web AS docs_italia_it_web_prod

COPY . /app

FROM docs_italia_it_build AS docs_italia_it_build_prod

COPY . /app
