from __future__ import absolute_import
from django.core.management.base import BaseCommand

from readthedocs.projects.models import Project
from elasticsearch import Elasticsearch, NotFoundError

es = Elasticsearch()


class Command(BaseCommand):

    """Removes projects without publisher from the ES index"""

    def handle(self, *args, **options):
        """handle command"""
        for p in Project.objects.filter(publisherproject__isnull=True):
            print(p.name)
            print(p.get_absolute_url())
            print(p.pk)
            if es.exists(index='readthedocs', doc_type='project', id=p.pk):
                es.delete(index='readthedocs', doc_type='project', id=p.pk)
            print('')

