# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from readthedocs.builds.models import Version
from readthedocs.docsitalia.models import Publisher, PublisherProject
from readthedocs.docsitalia.views.core_views import (
    DocsItaliaHomePage, PublisherIndex)
from readthedocs.projects.models import Project


class DocsItaliaViewsTest(TestCase):
    def test_docsitalia_homepage_get_queryset_filter_projects(self):
        hp = DocsItaliaHomePage()

        project = Project.objects.create(
            name='my project',
            slug='projectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )

        qs = hp.get_queryset()
        self.assertFalse(qs.exists())

        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            active=False
        )
        pub_project = PublisherProject.objects.create(
            name='Test Project',
            slug='testproject',
            metadata={
                'documents': [
                    'https://github.com/testorg/myrepourl',
                    'https://github.com/testorg/anotherrepourl',
                ]
            },
            publisher=publisher,
            active=False
        )
        pub_project.projects.add(project)

        qs = hp.get_queryset()
        self.assertFalse(qs.exists())

        # active publisher project, not active publisher
        pub_project.active = True
        pub_project.save()
        qs = hp.get_queryset()
        self.assertFalse(qs.exists())

        # active publisher, not active publisher project
        pub_project.active = False
        pub_project.save()
        publisher.active = True
        publisher.save()
        qs = hp.get_queryset()
        self.assertFalse(qs.exists())

        # active publisher, active publisher project, no public version
        pub_project.active = True
        pub_project.save()
        # a version for the project is already available
        version = Version.objects.first()
        version.privacy_level = 'private'
        version.save()
   
        qs = hp.get_queryset()
        self.assertFalse(qs.exists())

        # at last it should return our project
        version.privacy_level = 'public'
        version.save()
        qs = hp.get_queryset().values_list('pk')
        self.assertTrue(list(qs), [project.pk])

    def test_docsitalia_publisher_index_get_queryset_filter_active(self):
        index = PublisherIndex()

        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            active=False
        )

        qs = index.get_queryset()
        self.assertFalse(qs.exists())

        publisher.active = True
        publisher.save()

        qs = index.get_queryset()
        self.assertTrue(qs.exists())
