import os
import re

from .base import CommunityBaseSettings


class DocsItaliaSettings(CommunityBaseSettings):

    """Settings for DocsItalia"""

    # default build versions
    RTD_LATEST = 'bozza'
    RTD_LATEST_VERBOSE_NAME = RTD_LATEST
    RTD_STABLE = 'stabile'
    RTD_STABLE_VERBOSE_NAME = RTD_STABLE

    DEFAULT_PRIVACY_LEVEL = 'private'

    @property
    def INSTALLED_APPS(self):  # noqa
        apps = super(DocsItaliaSettings, self).INSTALLED_APPS
        # Insert our depends above RTD applications, after guaranteed third
        # party package
        apps.insert(apps.index('rest_framework'), 'docs_italia_convertitore_web')
        apps.insert(apps.index('rest_framework'), 'raven.contrib.django.raven_compat')
        return apps

    # Haystack - we don't really use it. ES API is used instead
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        },
    }

    CELERY_ALWAYS_EAGER = False
    CELERY_HAYSTACK_DEFAULT_ALIAS = None
    CELERY_TASK_RESULT_EXPIRES = 7200

    # Override classes
    CLASS_OVERRIDES = {
        'readthedocs.builds.syncers.Syncer': 'readthedocs.builds.syncers.LocalSyncer',
        'readthedocs.core.resolver.Resolver': 'readthedocs.docsitalia.resolver.ItaliaResolver',
        'readthedocs.oauth.services.GitHubService':
            'readthedocs.docsitalia.oauth.services.github.DocsItaliaGithubService',
    }

    TIME_ZONE = 'Europe/Rome'
    LANGUAGE_CODE = 'it-it'

    # Etc
    RESTRUCTUREDTEXT_FILTER_SETTINGS = {
        'cloak_email_addresses': True,
        'file_insertion_enabled': False,
        'raw_enabled': False,
        'strip_comments': True,
        'doctitle_xform': True,
        'sectsubtitle_xform': True,
        'initial_header_level': 2,
        'report_level': 5,
        'syntax_highlight': 'none',
        'math_output': 'latex',
        'field_name_limit': 50,
    }
    USE_PROMOS = False

    # Banned" projects
    HTML_ONLY_PROJECTS = (
        'atom',
        'galaxy-central',
        'django-geoposition',
    )

DocsItaliaSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from .local_settings import *  # noqa
    except ImportError:
        pass
