# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import mock
import requests_mock
from requests.exceptions import ConnectionError

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from readthedocs.builds.models import Build, Version
from readthedocs.docsitalia.github import InvalidMetadata
from readthedocs.docsitalia.models import Publisher, PublisherProject
from readthedocs.docsitalia.views.core_views import (
    DocsItaliaHomePage, PublisherIndex, PublisherProjectIndex, PublisherList)
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.models import Project
from readthedocs.search.indexes import PageIndex


DOCUMENT_METADATA = """document:
  name: Documento Documentato Pubblicamente
  description: |
    Lorem ipsum dolor sit amet, consectetur
  tags:
    - amazing document"""


class DocsItaliaViewsTest(TestCase):
    fixtures = ['eric']

    def setUp(self):
        eric = User.objects.get(username='eric')
        remote = RemoteRepository.objects.create(
            full_name='remote repo name',
            html_url='https://github.com/testorg/myrepourl',
            ssh_url='https://github.com/org-docs-italia/altro-progetto.git',
        )
        remote.users.add(eric)

        self.import_project_data = {
            'repo_type': 'git',
            'description': 'description',
            'remote_repository': str(remote.pk),
            'repo': 'https://github.com/org-docs-italia/altro-progetto.git',
            'project_url': 'https://github.com/org-docs-italia/altro-progetto',
            'name': 'altro-progetto'
        }
        self.document_settings_url = (
            'https://raw.githubusercontent.com/org-docs-italia/'
            'altro-progetto/master/document_settings.yml'
        )

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

        # no build is passed, so no project even if it is public
        version.privacy_level = 'public'
        version.save()
        qs = hp.get_queryset().values_list('pk')
        self.assertFalse(qs.exists())

        # let's create a build, but it is only triggered
        build = Build.objects.create(
            project=project,
            version=version,
            type='html',
            state='triggered',
        )
        build.save()
        self.assertFalse(qs.exists())

        # build is finished, but it is not passed
        build.state = 'finished'
        build.success = False
        build.save()
        self.assertFalse(qs.exists())

        # build is finally passed, so we have our project in homepage
        build.success = True
        build.save()
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

    def test_docsitalia_publisher_index_show_publisher_with_active_builds(self):
        index = PublisherIndex()

        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            active=True
        )

        inactive_pub_project = PublisherProject.objects.create(
            name='Inactive Project',
            slug='inactivetestproject',
            metadata={
                'documents': [
                    'https://github.com/testorg/myrepourl',
                    'https://github.com/testorg/anotherrepourl',
                ]
            },
            publisher=publisher,
            active=False
        )

        project = Project.objects.create(
            name='my project',
            slug='projectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        pub_project = PublisherProject.objects.create(
            name='Built Test Project',
            slug='builttestproject',
            metadata={
                'documents': [
                    'https://github.com/testorg/myrepourl',
                    'https://github.com/testorg/anotherrepourl',
                ]
            },
            publisher=publisher,
            active=True
        )
        pub_project.projects.add(project)

        no_build_project = Project.objects.create(
            name='no build project',
            slug='nobuildprojectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        no_build_project.versions.all().delete()
        pub_project_no_build = PublisherProject.objects.create(
            name='Test Project no build',
            slug='nobuildtestproject',
            metadata={
                'documents': [
                    'https://github.com/testorg/myrepourl',
                    'https://github.com/testorg/anotherrepourl',
                ]
            },
            publisher=publisher,
            active=True
        )
        pub_project_no_build.projects.add(no_build_project)

        response = self.client.get('/testorg/')
        self.assertContains(response, 'Built Test Project')
        self.assertNotContains(response, 'Inactive Project')
        self.assertNotContains(response, 'Test Project no build')

    def test_docsitalia_publisher_list_filters_active_publishers(self):
        publisher_list = PublisherList()

        Publisher.objects.create(
            name='No meta Org',
            slug='nometaorg',
            metadata={'some': 'meta'},
            active=False
        )
        Publisher.objects.create(
            name='Inactive Org',
            slug='inactiveorg',
            metadata={},
            active=False
        )
        Publisher.objects.create(
            name='Active Org',
            slug='activeorg',
            metadata={'some': 'meta'},
            active=True
        )
        publisher = Publisher.objects.create(
            name='Org',
            slug='testorg',
            metadata={'some': 'meta'},
            active=True
        )
        project = Project.objects.create(
            name='my project',
            slug='projectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        pub_project = PublisherProject.objects.create(
            name='Test Project',
            slug='testproject',
            publisher=publisher,
            active=True
        )
        pub_project.projects.add(project)
        version = project.versions.last()
        Build.objects.create(
            project=project,
            version=version,
            type='html',
            state='finished',
            success=True
        )

        qs = publisher_list.get_queryset()
        self.assertTrue(qs.exists())
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().pk, publisher.pk)

    def test_docsitalia_publisher_project_index_get_queryset_filter_active(self):
        index = PublisherProjectIndex()

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

        qs = index.get_queryset()
        self.assertFalse(qs.exists())

        publisher.active = True
        publisher.save()
        qs = index.get_queryset()
        self.assertFalse(qs.exists())

        pub_project.active = True
        pub_project.save()
        publisher.active = False
        publisher.save()
        qs = index.get_queryset()
        self.assertFalse(qs.exists())

        publisher.active = True
        publisher.save()
        qs = index.get_queryset()
        self.assertTrue(qs.exists())

    def test_docsitalia_import_render_error_without_metadata(self):
        self.client.login(username='eric', password='test')
        with requests_mock.Mocker() as rm:
            rm.get(self.document_settings_url, exc=ConnectionError)
            response = self.client.post(
                '/docsitalia/dashboard/import/', data=self.import_project_data)
        self.assertTemplateUsed(response, 'docsitalia/import_error.html')

    def test_docsitalia_import_render_error_with_invalid_metadata(self):
        self.client.login(username='eric', password='test')
        with requests_mock.Mocker() as rm:
            rm.get(self.document_settings_url, exc=InvalidMetadata)
            response = self.client.post(
                '/docsitalia/dashboard/import/', data=self.import_project_data)
        self.assertTemplateUsed(response, 'docsitalia/import_error.html')

    @mock.patch('readthedocs.docsitalia.views.core_views.trigger_build')
    def test_docsitalia_redirect_to_project_detail_with_valid_metadata(self, trigger_build):
        self.client.login(username='eric', password='test')
        with requests_mock.Mocker() as rm:
            rm.get(self.document_settings_url, text=DOCUMENT_METADATA)
            response = self.client.post(
                '/docsitalia/dashboard/import/', data=self.import_project_data)
        project = Project.objects.get(repo=self.import_project_data['repo'])
        repo = RemoteRepository.objects.get(ssh_url=project.repo)
        self.assertEqual(repo.project, project)
        redirect_url = reverse('projects_detail', kwargs={'project_slug': 'altro-progetto'})
        self.assertRedirects(response, redirect_url)

    @mock.patch('readthedocs.docsitalia.views.core_views.trigger_build')
    def test_docsitalia_import_render_error_for_invalid_fields(self, trigger_build):
        self.client.login(username='eric', password='test')
        with requests_mock.Mocker() as rm:
            rm.get(self.document_settings_url, text=DOCUMENT_METADATA)
            response = self.client.post(
                '/docsitalia/dashboard/import/', data=self.import_project_data)
            self.assertEqual(response.status_code, 302)
            response = self.client.post(
                '/docsitalia/dashboard/import/', data=self.import_project_data)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'docsitalia/import_error.html')

    def test_docsitalia_api_returns_400_without_project(self):
        response = self.client.get('/api/v2/docsearch/?q=query&project=projectslug&version=latest')
        self.assertEqual(response.status_code, 400)

    @mock.patch.object(PageIndex, 'search')
    def test_docsitalia_api_returns_404_without_results(self, search):
        search.return_value = None
        project = Project.objects.create(
            name='my project',
            slug='projectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        response = self.client.get('/api/v2/docsearch/?q=query&project=projectslug&version=latest')
        self.assertEqual(response.status_code, 404)

    @mock.patch.object(PageIndex, 'search')
    def test_docsitalia_api_returns_results(self, search):
        search.return_value = {}
        project = Project.objects.create(
            name='my project',
            slug='projectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        response = self.client.get('/api/v2/docsearch/?q=query&project=projectslug&version=latest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), {'results': {}})
