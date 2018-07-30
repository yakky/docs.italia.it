"""Removes projects without publisher from the ES index"""
from __future__ import (
    absolute_import, print_function)

from django.core.management.base import BaseCommand

from elasticsearch import Elasticsearch
from readthedocs.projects.models import Project


class Command(BaseCommand):

    """Removes projects without publisher from the ES index"""

    def handle(self, *args, **options):
        """handle command"""
        e_s = Elasticsearch()
        for p_o in Project.objects.filter(publisherproject__isnull=True):
            print(p_o.name)
            print(p_o.get_absolute_url())
            print(p_o.pk)
            if e_s.exists(index='readthedocs', doc_type='project', id=p_o.pk):
                e_s.delete(index='readthedocs', doc_type='project', id=p_o.pk)
            print('')
