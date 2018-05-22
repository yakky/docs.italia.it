# -*- coding: utf-8 -*-
"""Signals for the docsitalia app."""

from __future__ import absolute_import

import logging

from django.dispatch import receiver

from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.signals import project_import

from .github import get_metadata_for_document
from .models import PublisherProject


log = logging.getLogger(__name__) # noqa


@receiver(project_import)
def on_project_import(sender, **kwargs): # noqa
    """
    Main entry point for Project related customizations

    After a Project is imported we need to do a couple of things, hooking
    to this signal permits us to avoid messing with RTD code.
    First we connect a Project to its PublisherProject, and that's the
    easy part.
    Then we need to update the Project model with the data we have in the
    document_settings.yml. We don't care much about what it's in the model
    and we consider the config file as source of truth.
    """
    project = sender

    try:
        remote = RemoteRepository.objects.get(project=project)
    except RemoteRepository.DoesNotExist:
        log.error('Missing RemoteRepository for project {}'.format(project))
    else:
        pub_projects = PublisherProject.objects.filter(
            metadata__documents__contains=[remote.html_url]
        )
        for pub_proj in pub_projects:
            pub_proj.projects.add(project)

    try:
        # we take the file via http because we don't have a checkout
        metadata = get_metadata_for_document(project)
    except Exception as e: # noqa
        log.error(
            'Failed to import document metadata: %s', e)
    else:
        document = metadata['document']
        project.name = document['name']
        project.description = document['description']
        project.tags.set(*document['tags'], clear=True)
        project.save()
