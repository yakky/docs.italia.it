# -*- coding: utf-8 -*-
"""Signals for the docsitalia app."""

from __future__ import absolute_import

import logging

from django.dispatch import receiver
from django.db.models.signals import pre_delete

from readthedocs.core.signals import webhook_github
from readthedocs.doc_builder.signals import finalize_sphinx_context_data

from .github import get_metadata_for_document
from .models import PublisherProject, update_project_from_metadata


log = logging.getLogger(__name__) # noqa


@receiver(webhook_github)
def on_webhook_github(sender, project, data, event, **kwargs): # noqa
    # no push no party
    if event != 'push':
        return

    try:
        branch = data['ref'].replace('refs/heads/', '')
    except KeyError:
        log.error(
            'metadata github hook: Parameter "ref" is required')
        return

    if branch != 'master':
        log.info('Skipping metadata update for project: project=%s branch=%s',
                 project, branch)
        return

    try:
        metadata = get_metadata_for_document(project)
    except Exception as e: # noqa
        log.error(
            'Failed to import document metadata: %s', e)
    else:
        update_project_from_metadata(project, metadata)


@receiver(finalize_sphinx_context_data)
def add_sphinx_context_data(sender, data, build_env, **kwargs):  # pylint: disable=unused-argument
    """
    Provides additional data to the sphinx context

    Data are injected in the provided context

    :param sender: sender class
    :param data: sphinx context
    :param build_env: BuildEnvironment instance
    :return: None
    """
    from readthedocs.docsitalia.utils import get_subprojects

    subprojects = get_subprojects(build_env.project.pk)
    data['subprojects'] = subprojects
    publisher_project = build_env.project.publisherproject_set.first()
    data['publisher_project'] = publisher_project
    data['publisher'] = publisher_project.publisher if publisher_project else None


@receiver(pre_delete, sender=PublisherProject)
def on_publisher_project_delete(sender, instance, **kwargs):  # noqa
    """Remove all the projects associated at PublisherProject removal from db and ES indexes"""
    from readthedocs.docsitalia.tasks import clear_es_index
    projects_pks = list(instance.projects.values_list('pk', flat=True))
    instance.projects.all().delete()
    clear_es_index.delay(projects=projects_pks)
