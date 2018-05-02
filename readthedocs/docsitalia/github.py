"""Github related utils"""

from __future__ import absolute_import

import requests

from readthedocs.docsitalia.models import SETTINGS_VALIDATORS


METADATA_BASE_URL = (
    'https://raw.githubusercontent.com/{org}/{repo}/master/{settings}'
)


class InvalidMetadata(Exception):

    """Invalid metadata generic exception"""

    pass


def build_metadata_url(org, repo, settings):
    """Builds the url for a specific metadata settings file"""
    url = METADATA_BASE_URL.format(
        org=org, repo=repo, settings=settings)
    return url


def get_metadata_from_url(url, session=None):
    """Gets an url via a requests compatible api"""
    if not session:
        session = requests
    response = session.get(url)
    return response.text


def get_metadata_for_publisher(org, publisher, settings, session=None):
    """Fetch and validate metadata for a specific settings file"""
    url = build_metadata_url(
        org=org.slug,
        repo=publisher.config_repo_name,
        settings=settings)
    data = get_metadata_from_url(url, session=session)

    if not data:
        msg = 'no {} metadata for {}'.format(settings, publisher)
        raise InvalidMetadata(msg)

    validator = SETTINGS_VALIDATORS[settings]
    try:
        metadata = validator(org, data)
    except ValueError:
        msg = 'invalid {} metadata for {}'.format(settings, publisher)
        raise InvalidMetadata(msg)

    return metadata
