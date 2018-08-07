"""Docs Italia tasks."""

from __future__ import unicode_literals
import logging

from django.conf import settings
from elasticsearch import Elasticsearch, exceptions

from readthedocs.worker import app


log = logging.getLogger(__name__)  # noqa


@app.task()
def clear_es_index(projects):
    """Clearing ES indexes for removed projects"""
    projects_str = ', '.join([str(p) for p in projects])
    log.info('Clearing indexes for removed projects: %s', projects_str)
    e_s = Elasticsearch(settings.ES_HOSTS)
    for p_id in projects:
        try:
            e_s.delete(index='readthedocs', doc_type='project', id=p_id)
        except exceptions.NotFoundError:
            pass

        try:
            e_s.delete_by_query(
                index='readthedocs',
                doc_type='page',
                body={'query': {'term': {'project_id': p_id}}})
        except exceptions.NotFoundError:
            pass
