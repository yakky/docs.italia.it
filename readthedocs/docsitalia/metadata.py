# -*- coding: utf-8 -*-
"""Metadata utils for the docsitalia app."""

from django.utils.text import slugify

from .models import AllowedTag
from .utils import load_yaml

PUBLISHER_SETTINGS = 'publisher_settings.yml'
PROJECTS_SETTINGS = 'projects_settings.yml'
DOCUMENT_SETTINGS = 'document_settings.yml'

PUBLISHER_REQUIRED_FIELDS = 'name', 'description'
PROJECT_REQUIRED_FIELDS = 'name', 'description', 'documents'
DOCUMENT_REQUIRED_FIELDS = 'name', 'description', 'tags'


RAW_GITHUB_BASE_URL = (
    'https://raw.githubusercontent.com/{org}/{repo}/master/{path}'
)


class InvalidMetadata(Exception):

    """Invalid metadata generic exception"""

    pass


def validate_publisher_metadata(org, settings, **kwargs): # noqa
    """Validate the publisher metadata"""
    data = load_yaml(settings)
    try:
        publisher = data['publisher']
        for field in PUBLISHER_REQUIRED_FIELDS:
            if not publisher[field]:
                raise ValueError('Missing required field "%s" in %s' % (field, publisher))
        # expand the logo url and store it in the metadata
        model = kwargs.get('model')
        logo = publisher.get('logo')
        if model and logo:
            # TODO: will need some refactoring when going multi platform
            publisher['logo_url'] = RAW_GITHUB_BASE_URL.format(
                org=model.slug,
                repo=model.config_repo_name,
                path=logo.lstrip('/')
            )
    except (KeyError, TypeError):
        raise ValueError('General error in parsing publisher metadata %s' % data)
    return data


def validate_projects_metadata(org, settings, **kwargs): # noqa
    """Validate the projects metadata"""
    data = load_yaml(settings)
    try:
        projects = data['projects']
        for project in projects:
            # required values for a well formed configuration
            for field in PROJECT_REQUIRED_FIELDS:
                if not project[field]:
                    raise ValueError('Missing required field "%s" in %s' % (field, project))
            if not project['documents'][0]:
                raise ValueError('Missing required field "%s" in %s' % ('documents', project))
            for index, document in enumerate(project['documents']):
                # expand the document repository to an url so it's easier to query at
                # Project import time
                project['documents'][index] = {
                    'repository':  document,
                    'repo_url': '{}/{}'.format(org.url, document)
                }
            name_for_slug = project.get('short_name', project['name'])
            project['slug'] = slugify(name_for_slug)
    except (KeyError, TypeError):
        raise ValueError('General error in parsing projects metadata %s' % data)
    return data


def validate_document_metadata(org, settings, **kwargs): # noqa
    """Validate the document metadata"""
    data = load_yaml(settings)
    try:
        document = data['document']
        for field in DOCUMENT_REQUIRED_FIELDS:
            if not document[field]:
                raise ValueError('Missing required field "%s" in %s' % (field, document))
    except (KeyError, TypeError):
        raise ValueError('General error in parsing document metadata %s' % data)
    data = _remove_invalid_tags(data)
    return data


def _remove_invalid_tags(data):
    allowed_tags = set(AllowedTag.objects.filter(enabled=True).values_list('name', flat=True))
    original_tags = {tag.strip().lower() for tag in data['document']['tags']}
    new_tags = list(original_tags & allowed_tags)
    data['document']['tags'] = new_tags
    return data


SETTINGS_VALIDATORS = {
    PUBLISHER_SETTINGS: validate_publisher_metadata,
    PROJECTS_SETTINGS: validate_projects_metadata,
    DOCUMENT_SETTINGS: validate_document_metadata,
}
