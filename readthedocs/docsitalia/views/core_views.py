# -*- coding: utf-8 -*-
"""Public project views."""

from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView, View

from readthedocs.core.utils import trigger_build
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.forms import ProjectBasicsForm, ProjectExtraForm
from readthedocs.projects.models import Project
from readthedocs.projects.signals import project_import
from readthedocs.projects.views.private import ImportView

from ..github import get_metadata_for_document
from ..metadata import InvalidMetadata
from ..models import PublisherProject, Publisher, update_project_from_metadata
from ..utils import get_projects_with_builds

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
        - Build is success and finished
        """
        active_pub_projects = PublisherProject.objects.filter(
            active=True,
            publisher__active=True
        )
        qs = get_projects_with_builds()
        return qs.filter(
            publisherproject__in=active_pub_projects
        ).order_by(
            '-modified_date', '-pub_date'
        )[:24]


class PublisherList(ListView):  # pylint: disable=too-many-ancestors

    """List view of :py:class:`Publisher` instances."""

    model = Publisher

    def get_queryset(self):
        """
        Filter publisher to be listed

        We show publishers that matches the following requirements:
        - are active
        - have documents with successful public build
        """
        active_pub_projects = PublisherProject.objects.filter(
            active=True,
            publisher__active=True
        )
        publishers_with_projects = get_projects_with_builds().filter(
            publisherproject__in=active_pub_projects
        ).values_list(
            'publisherproject__publisher',
            flat=True
        )

        return Publisher.objects.filter(
            pk__in=publishers_with_projects
        )


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


class DocumentRedirect(View):

    """Redirect unversioned / unlanguaged urls to the canonical document URL"""

    def get_queryset(self):
        """Filter projects based on user permissions"""
        return Project.objects.protected(self.request.user)

    def get(self, request, *args, **kwargs):  # noqa
        """Redirect to the canonical URL of the document"""
        try:
            document = self.get_queryset().get(slug=self.kwargs['slug'])
            return HttpResponseRedirect(document.get_docs_url(lang_slug=self.kwargs.get('lang')))
        except Project.DoesNotExist:
            raise Http404()


class DocsItaliaImport(ImportView):  # pylint: disable=too-many-ancestors

    """Simplified ImportView for Docs Italia"""

    def post(self, request, *args, **kwargs):  # noqa

        """
        Handler for Project import

        We import the Project only after validating the mandatory metadata.
        We then connect a Project to its PublisherProject.
        Finally we need to update the Project model with the data we have in the
        document_settings.yml. We don't care much about what it's in the model
        and we consider the config file as source of truth.
        """
        form = ProjectBasicsForm(request.POST, user=request.user)

        if not form.is_valid():
            return render(request, 'docsitalia/import_error.html', {'error_list': form.errors})

        project = form.save()

        # try to get the document metadata from github
        try:
            metadata = get_metadata_for_document(project)
        except InvalidMetadata as exception:
            log.error('Failed to import document invalid metadata %s', exception)
            msg = _('Invalid document_settings.yml found in the repository')
            project.delete()
            return render(request, 'docsitalia/import_error.html', {'error_msg': msg})
        except Exception as e:  # noqa
            log.error(
                'Failed to import document metadata: %s', e)
            msg = _('Failed to download document_settings.yml from the repository')
            project.delete()
            return render(request, 'docsitalia/import_error.html', {'error_msg': msg})

        extra_fields = ProjectExtraForm.Meta.fields
        for field, value in request.POST.items():
            if field in extra_fields:
                setattr(project, field, value)
        project.save()
        project.users.add(request.user)

        # link the document to the project
        try:
            remote = RemoteRepository.objects.get(project=project)
        except RemoteRepository.DoesNotExist:
            log.error('Missing RemoteRepository for project {}'.format(project))
        else:
            pub_projects = PublisherProject.objects.filter(
                metadata__documents__contains=[{'repo_url': remote.html_url}]
            )
            for pub_proj in pub_projects:
                pub_proj.projects.add(project)
            if not pub_projects:
                log.error('No PublisherProject found for repo {}'.format(remote.html_url))

        # and finally update the Project model with the metadata
        update_project_from_metadata(project, metadata)

        project_import.send(sender=project, request=self.request)
        trigger_build(project, basic=True)
        return redirect('projects_detail', project_slug=project.slug)
