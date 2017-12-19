# -*- coding: utf-8 -*-
"""Reindex Elastic Search indexes."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
import socket
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.tasks import update_search

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            dest='project',
            default='',
            help='Project to index'
        )
        parser.add_argument(
            '-l',
            dest='only_latest',
            default=False,
            action='store_true',
            help='Only index latest'
        )

    def handle(self, *args, **options):
        """Build/index all versions or a single project's version."""
        project = options['project']
        only_latest = options['only_latest']

        queryset = Version.objects.filter(active=True)

        if project:
            queryset = queryset.filter(project__slug=project)
            if not queryset.exists():
                raise CommandError(
                    u'No project with slug: {slug}'.format(slug=project))
            log.info(u'Building all versions for %s', project)
        if only_latest:
            log.warning('Indexing only latest')
            queryset = queryset.filter(slug=LATEST)

        for version in queryset:
            log.info("Reindexing %s", version)
            try:
                commit = version.project.vcs_repo(version.slug).commit
            except:  # noqa
                # An exception can be thrown here in production, but it's not
                # documented what the exception here is
                commit = None

            try:
                update_search.apply_async(
                    args=[version.pk, commit],
                    kwargs=dict(delete_non_commit_files=False),
                    priority=0,
                    queue=socket.gethostname()
                )
            except Exception as e:
                log.exception('Reindex failed for %s, %s', version, e)
