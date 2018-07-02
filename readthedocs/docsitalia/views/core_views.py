# -*- coding: utf-8 -*-
"""Public project views."""

from __future__ import absolute_import
from __future__ import unicode_literals

from django.views.generic import DetailView, ListView

from readthedocs.builds.models import Version
from readthedocs.docsitalia.models import PublisherProject, Publisher
from readthedocs.projects.models import Project


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
