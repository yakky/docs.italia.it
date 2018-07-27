# -*- coding: utf-8 -*-
"""Delete and Reindex Elastic Search indexes."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
from optparse import make_option

from django.conf import settings
from elasticsearch import Elasticsearch

from readthedocs.core.management.commands.reindex_elasticsearch import (
    Command as ReindexElasticsearch
)
from readthedocs.search.indexes import Index

log = logging.getLogger(__name__)


class Command(ReindexElasticsearch):
    option_list = ReindexElasticsearch.option_list + (
        make_option('--delete-index',
                    dest='delete',
                    default=False,
                    action='store_true',
                    help='Delete the index before reindexing'),
    )

    def handle(self, *args, **options):
        """Same as RTD reindex_elasticsearch but with a switch to delete the index"""
        delete = options.get('delete')
        if delete:
            log.info(u'Delete the index %s', Index._index)
            es = Elasticsearch(settings.ES_HOSTS)
            es.delete(index=Index._index)
        del options['delete']
        super(Command, self).handle(*args, **options)
