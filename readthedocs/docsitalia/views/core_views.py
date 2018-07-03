# -*- coding: utf-8 -*-
"""Public project views."""

from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView

from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.forms import ProjectBasicsForm, ProjectExtraForm
from readthedocs.projects.models import Project
from readthedocs.projects.signals import project_import
from readthedocs.projects.views.private import ImportView

from ..github import get_metadata_for_document, InvalidMetadata
from ..models import PublisherProject, Publisher

log = logging.getLogger(__name__)  # noqa


class DocsItaliaHomePage(ListView):  # pylint: disable=too-many-ancestors

    """Docs italia Home Page"""

    model = Project
    template_name = 'docsitalia/docsitalia_homepage.html'

    def get_queryset(self):
        """
        Filter projects to show in homepage

        We show in homepage projects that matches the following requirements:
        - Publisher is active
        - PublisherProject is active
        - document (Project) has a public build
        """
        active_pub_projects = PublisherProject.objects.filter(
            active=True,
            publisher__active=True
        )
        with_public_version = Version.objects.filter(
            privacy_level='public',
            active=True,
        ).values_list(
            'project',
            flat=True
        )
        return Project.objects.filter(
            pk__in=with_public_version
        ).filter(
            publisherproject__in=active_pub_projects
        ).order_by(
            '-modified_date', '-pub_date'
        )[:24]


class PublisherIndex(DetailView):  # pylint: disable=too-many-ancestors

    """Detail view of :py:class:`Publisher` instances."""

    model = Publisher

    def get_queryset(self):
        """Filter for active Publisher"""
        return Publisher.objects.filter(active=True)


class PublisherProjectIndex(DetailView):  # pylint: disable=too-many-ancestors

    """Detail view of :py:class:`PublisherProject` instances."""

    model = PublisherProject

    def get_queryset(self):
        """Filter for active PublisherProject"""
        return PublisherProject.objects.filter(
            active=True,
            publisher__active=True
        )


class DocsItaliaImport(ImportView):  # pylint: disable=too-many-ancestors

    """Simplified ImportView for Docs Italia"""

    def post(self, request, *args, **kwargs):
        """Validate metadata before importing the project"""
        form = ProjectBasicsForm(request.POST, user=request.user)
        project = form.save(commit=False)

        try:
            get_metadata_for_document(project)
        except InvalidMetadata:
            log.error(
                'Failed to import document invalid metadata')
            msg = _('Invalid document_settings.yml found in the repository')
            return render(request, 'docsitalia/import_error.html', {'error_msg': msg})
        except Exception as e: # noqa
            log.error(
                'Failed to import document metadata: %s', e)
            msg = _('Failed to download document_settings.yml from the repository')
            return render(request, 'docsitalia/import_error.html', {'error_msg': msg})

        extra_fields = ProjectExtraForm.Meta.fields
        for field, value in request.POST.items():
            if field in extra_fields:
                setattr(project, field, value)
        project.save()
        project.users.add(request.user)

        # FIXME: move what we are doing in our signal handler here
        project_import.send(sender=project, request=self.request)
        trigger_build(project, basic=True)
        return redirect('projects_detail', project_slug=project.slug)
