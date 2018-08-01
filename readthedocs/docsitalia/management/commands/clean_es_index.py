"""Removes projects without publisher from the ES index"""
from __future__ import (
    absolute_import, print_function)

from django.db.models import Q
from django.core.management.base import BaseCommand
from django.conf import settings

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from readthedocs.projects.models import Project

from readthedocs.docsitalia.models import PublisherProject


class Command(BaseCommand):

    """
    Clean ES index:

    Removes projects without publisher or inactive publisher or
    inactive publisher project from the ES index.
    Delete projects not linked to a publisher project from the db.
    """

    def handle(self, *args, **options):
        """handle command"""
        e_s = Elasticsearch(settings.ES_HOSTS)
        inactive_pp = PublisherProject.objects.filter(
            Q(active=False) | Q(publisher__active=False)
        ).values_list('pk', flat=True)
        queryset = Project.objects.filter(
            Q(publisherproject__isnull=True) | Q(publisherproject__in=inactive_pp)
        )
        for p_o in queryset:
            print(p_o.name, p_o.get_absolute_url(), p_o.pk)
            try:
                e_s.delete(index='readthedocs', doc_type='project', id=p_o.pk)
            except NotFoundError:
                print('Index not found')
            try:
                e_s.delete_by_query(
                    index='readthedocs', doc_type='page',
                    body={'query': {'term': {'project_id': p_o.pk}}}
                )
            except NotFoundError:
                print('Index not found')
            print('')
        Project.objects.filter(publisherproject__isnull=True).delete()
