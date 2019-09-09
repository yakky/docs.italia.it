FROM python:3.6-slim AS docs_italia_it_base

ENV DEBIAN_FRONTEND noninteractive

RUN python -mvenv /virtualenv

RUN apt update

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

FROM docs_italia_it_base AS docs_italia_it_web

RUN apt purge -y build-essential && apt autoremove -y && apt clean

CMD ["/bin/bash"]

FROM docs_italia_it_base AS docs_italia_it_build

RUN apt install --no-install-recommends -y \
    python2.7 \
    python2.7-dev \
    python-pip \
    python-virtualenv \
    texlive-generic-recommended \
    texlive-latex-recommended \
    texlive-extra-utils \
    libfreetype6 g++ sqlite libevent-dev libffi-dev \
    libenchant1c2a curl python-m2crypto python-matplotlib \
    python-numpy python-scipy python-pandas graphviz graphviz-dev \
    libgraphviz-dev pandoc doxygen  python3 python3-dev python3-pip \
    python3-matplotlib python3-numpy python3-scipy python3-pandas \
    texlive-latex-extra pkg-config libjpeg-dev \
    libfreetype6-dev libtiff5-dev zlib1g-dev liblcms2-dev \
    libwebp-dev libcairo2-dev

RUN apt-get install texlive-fonts-recommended -y

RUN apt autoremove -y && apt clean

CMD ["/bin/bash"]
