# -*- coding: utf-8 -*-
"""AppConfig for the docsitalia app."""

from django.apps import AppConfig


class DocsItaliaConfig(AppConfig):

    """docsitalia app config"""

    name = 'readthedocs.docsitalia'
    verbose_name = 'Docs Italia'

    def ready(self): # noqa
        import readthedocs.docsitalia.signals # noqa
