"""Remove the readthedocs elasticsearch index"""

from __future__ import absolute_import

from django.conf import settings
from django.core.management.base import BaseCommand

from elasticsearch import Elasticsearch


class Command(BaseCommand):

    """Clear elasticsearch index"""

    def handle(self, *args, **options):
        """handle command"""
        e_s = Elasticsearch(settings.ES_HOSTS)
        e_s.indices.delete(index='readthedocs')
