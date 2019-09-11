"""Provision Elastic Search"""

from __future__ import absolute_import
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from elasticsearch import Elasticsearch
from readthedocs.search.indexes import Index, PageIndex, ProjectIndex, SectionIndex

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '--ensure-no-index', default=False, action='store_true',
            help='Perform provisioning only if no index exists yet.',
        )

    def handle(self, *args, **options):
        if options['ensure_no_index'] and self._index_exists():
            log.info(
                'Skipping provisioning: at least one index exists already.',
            )
            return
        self._provision_es()

    def _index_exists(self):
        indexes = len(Elasticsearch(settings.ES_HOSTS).indices.get_alias())
        return bool(indexes)

    def _provision_es(self):
        """Provision new ES instance"""
        index = Index()
        index_name = index.timestamped_index()

        log.info("Creating indexes..")
        index.create_index(index_name)
        index.update_aliases(index_name)

        log.info("Updating mappings..")
        proj = ProjectIndex()
        proj.put_mapping()
        page = PageIndex()
        page.put_mapping()
        sec = SectionIndex()
        sec.put_mapping()
        log.info("Done!")
