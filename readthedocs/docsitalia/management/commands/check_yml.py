# -*- coding: utf-8 -*-
"""Command that check local docs-italia-conf yml file"""

from __future__ import absolute_import, print_function, unicode_literals

from collections import namedtuple
from enum import Enum

from django.core.management.base import BaseCommand

from readthedocs.docsitalia.github import parse_metadata, get_metadata_from_url


class YmlType(Enum):

    """Enum class for yml file types"""

    publisher = 'publisher'
    project = 'project'
    document = 'document'

    def __str__(self):
        """Value of the type instance"""
        return self.value

    @property
    def yml_file(self):
        """Return the yml file matching the given type"""
        return dict(
            publisher='publisher_settings.yml',
            project='projects_settings.yml',
            document='document_settings.yml'
        )[self.value]


class Command(BaseCommand):

    """Command that check local docs-italia-conf yml file"""

    help = 'Check yml file.'

    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument('--yml', required=True)
        parser.add_argument('--type', type=YmlType, choices=list(YmlType), required=True)

    def handle(self, *args, **options):
        """Validate and output yml content"""
        file_path = options.get('yml')
        if file_path.startswith('http'):
            data = get_metadata_from_url(file_path)
        else:
            with open(file_path, 'r') as prj:
                data = prj.read()

        Org = namedtuple('Org', 'url')  # noqa
        org = Org('http://fake_url')
        data = parse_metadata(data, org, None, options.get('type').yml_file)
        print(data)
