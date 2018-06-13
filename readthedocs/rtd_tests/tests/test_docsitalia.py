from __future__ import absolute_import, unicode_literals

import requests
import requests_mock
from django.test.utils import override_settings

from mock import patch
import pytest

from django.conf import settings
from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template.loader import get_template
from rest_framework.response import Response

from readthedocs.builds.constants import LATEST
from readthedocs.core.signals import webhook_github
from readthedocs.docsitalia.resolver import ItaliaResolver
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import Project
from readthedocs.projects.signals import project_import

from readthedocs.docsitalia.oauth.services.github import DocsItaliaGithubService
from readthedocs.docsitalia.models import (
    Publisher, PublisherProject, PublisherIntegration,
    validate_publisher_metadata, validate_projects_metadata,
    validate_document_metadata)


PUBLISHER_METADATA = """publisher:
  name: Ministero della Documentazione Pubblica
  short-name: Min. Doc. Pub.
  description: |
    Lorem ipsum dolor sit amet, consectetur 
    adipisicing elit, sed do eiusmod tempor
    incididunt ut labore et dolore magna aliqua. 
    Ut enim ad minim veniam, quis nostrud 
    exercitation ullamco laboris nisi ut 
    aliquip ex ea commodo consequat.
    Duis aute irure dolor in reprehenderit in 
    voluptate velit esse cillum dolore eu
    fugiat nulla pariatur. Excepteur sint 
    occaecat cupidatat non proident, sunt in
    culpa qui officia deserunt mollit anim id 
    est laborum.
  website: https://www.ministerodocumentazione.gov.it
  tags:
    - documents
    - public
    - amazing publisher
  assets:
    logo: assets/images/logo.svg"""


PROJECTS_METADATA = """projects:
  - title: Progetto Documentato Pubblicamente
    short-name: PDP
    description: |
      Lorem ipsum dolor sit amet, consectetur 
      adipisicing elit, sed do eiusmod tempor
      incididunt ut labore et dolore magna aliqua. 
      Ut enim ad minim veniam, quis nostrud 
      exercitation ullamco laboris nisi ut 
      aliquip ex ea commodo consequat.
      Duis aute irure dolor in reprehenderit in 
      voluptate velit esse cillum dolore eu
      fugiat nulla pariatur. Excepteur sint 
      occaecat cupidatat non proident, sunt in
      culpa qui officia deserunt mollit anim id 
      est laborum.
    website: https://progetto.ministerodocumentazione.gov.it
    tags:
      - digital
      - citizenship
      - amazing project
    documents:
      - title: Documento del progetto
        repository: project-document-doc"""


DOCUMENT_METADATA = """document:
  name: Documento Documentato Pubblicamente
  description: |
    Lorem ipsum dolor sit amet, consectetur
  tags:
    - amazing document"""

IT_RESOLVER_IN_SETTINGS = 'readthedocs.docsitalia.resolver.ItaliaResolver'\
in getattr(settings, 'CLASS_OVERRIDES', {}).values()

class DocsItaliaTest(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.service = DocsItaliaGithubService(user=self.user, account=None)
        self.factory = RequestFactory()

    def test_make_organization_fail_without_publisher(self):
        org_json = {
            'html_url': 'https://github.com/testorg',
            'name': 'Test Org',
            'email': 'test@testorg.org',
            'login': 'testorg',
            'avatar_url': 'https://images.github.com/foobar',
        }
        Publisher.objects.create(
            name='Test Org',
            slug='adifferentorganization',
            metadata={},
            projects_metadata={},
            active=True
        )
        org = self.service.create_organization(org_json)
        self.assertIsNone(org)

    def test_make_organization_fail_with_publisher_not_active(self):
        org_json = {
            'html_url': 'https://github.com/testorg',
            'name': 'Test Org',
            'email': 'test@testorg.org',
            'login': 'testorg',
            'avatar_url': 'https://images.github.com/foobar',
        }
        Publisher.objects.create(
            name='Test Org',
            slug=org_json['login'],
            metadata={},
            projects_metadata={},
            active=False
        )
        org = self.service.create_organization(org_json)
        self.assertIsNone(org)

    def test_make_organization_works_with_publisher(self):
        org_json = {
            'html_url': 'https://github.com/testorg',
            'name': 'Test Org',
            'email': 'test@testorg.org',
            'login': 'testorg',
            'avatar_url': 'https://images.github.com/foobar',
        }
        publisher = Publisher.objects.create(
            name='Test Org',
            slug=org_json['login'],
            metadata={},
            projects_metadata={},
            active=True
        )
        org = self.service.create_organization(org_json)
        self.assertIsInstance(org, RemoteOrganization)
        self.assertEqual(org.slug, 'testorg')
        self.assertEqual(org.name, 'Test Org')
        self.assertEqual(org.email, 'test@testorg.org')
        self.assertEqual(org.avatar_url, 'https://images.github.com/foobar')
        self.assertEqual(org.url, 'https://github.com/testorg')

        user_in_org = org.users.filter(pk=self.user.pk)
        self.assertTrue(user_in_org.exists())

        publisher.refresh_from_db()
        self.assertTrue(publisher.remote_organization)
        self.assertEqual(publisher.remote_organization.pk, org.pk)

    def test_sync_organizations_works(self):
        orgs_json = [
            {'url': 'https://api.github.com/orgs/testorg'},
        ]
        org_json = {
            'html_url': 'https://github.com/testorg',
            'name': 'Test Org',
            'email': 'test@testorg.org',
            'login': 'testorg',
            'avatar_url': 'https://images.github.com/foobar',
        }
        org_repos_json = [{
            'name': 'testrepo',
            'full_name': 'testorg/testrepo',
            'description': 'Test Repo',
            'git_url': 'git://github.com/testorg/testrepo.git',
            'private': False,
            'ssh_url': 'ssh://git@github.com:testorg/testrepo.git',
            'html_url': 'https://github.com/testorg/testrepo',
            'clone_url': 'https://github.com/testorg/testrepo.git',
        }, {
            'name': 'project-document-doc',
            'full_name': 'testorg/project-document-doc',
            'description': 'Project document doc',
            'git_url': 'git://github.com/testorg/project-document-doc.git',
            'private': False,
            'ssh_url': 'ssh://git@github.com:testorg/project-document-doc.git',
            'html_url': 'https://github.com/testorg/project-document-doc',
            'clone_url': 'https://github.com/testorg/project-document-doc.git',
        }]
        publisher = Publisher.objects.create(
            name='Test Org',
            slug=org_json['login'],
            metadata={},
            projects_metadata={},
            active=True
        )
        session = requests.Session()
        with patch(
            'readthedocs.docsitalia.oauth.services.github.DocsItaliaGithubService.get_session') as m:
            m.return_value = session
            with requests_mock.Mocker() as rm:
                rm.get('https://api.github.com/user/orgs', json=orgs_json)
                rm.get('https://api.github.com/orgs/testorg', json=org_json)
                rm.get(
                    'https://raw.githubusercontent.com/testorg/'
                    'docs-italia-conf/master/publisher_settings.yml',
                    text=PUBLISHER_METADATA)
                rm.get(
                    'https://raw.githubusercontent.com/testorg/'
                    'docs-italia-conf/master/projects_settings.yml',
                    text=PROJECTS_METADATA)
                rm.get('https://api.github.com/orgs/testorg', json=org_json)
                rm.get('https://api.github.com/orgs/testorg/repos', json=org_repos_json)
                rm.post('https://api.github.com/repos/testorg/docs-italia-conf/hooks', json={})
                self.service.sync_organizations()

        projects = PublisherProject.objects.filter(publisher=publisher)
        self.assertEqual(projects.count(), 1)

        remote_repos = RemoteRepository.objects.all()
        self.assertEqual(remote_repos.count(), 1)

    @patch('django.contrib.messages.api.add_message')
    def test_project_import_signal_works(self, add_message):
        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            active=True
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
            active=True
        )

        project = Project.objects.create(
            name='my project',
            slug='myprojectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        remote = RemoteRepository.objects.create(
            full_name='remote repo name',
            html_url='https://github.com/testorg/myrepourl',
            project=project,
        )
        request = self.factory.get('/')
        request.user = self.user
        with requests_mock.Mocker() as rm:
            rm.get(
                'https://raw.githubusercontent.com/testorg/'
                'myrepourl/master/document_settings.yml',
                text='')
            project_import.send(sender=project, request=request)

        project_for_pub_project = pub_project.projects.filter(pk=project.pk)
        self.assertTrue(project_for_pub_project.exists())
        self.assertEqual(pub_project.projects.count(), 1)

        other_project = Project.objects.create(
            name='my other project',
            slug='myotherprojectslug',
            repo='https://github.com/testorg/myotherproject.git'
        )
        with requests_mock.Mocker() as rm:
            rm.get(
                'https://raw.githubusercontent.com/testorg/'
                'myotherproject/master/document_settings.yml',
                text='')
        project_import.send(sender=other_project, request=request)

        self.assertEqual(pub_project.projects.count(), 1)

    @patch('django.contrib.messages.api.add_message')
    def test_project_import_parse_document_metadata_correctly(self, add_message):
        project = Project.objects.create(
            name='my project',
            slug='myprojectslug',
            description='mydescription',
            repo='https://github.com/testorg/myrepourl.git'
        )
        request = self.factory.get('/')
        request.user = self.user
        with requests_mock.Mocker() as rm:
            rm.get(
                'https://raw.githubusercontent.com/testorg/'
                'myrepourl/master/document_settings.yml',
                text=DOCUMENT_METADATA)
            project_import.send(sender=project, request=request)
        project.refresh_from_db()
        self.assertEqual(project.name, 'Documento Documentato Pubblicamente')
        self.assertEqual(project.description, 'Lorem ipsum dolor sit amet, consectetur\n')
        self.assertEqual(project.tags.count(), 1)
        self.assertIn('amazing-document', project.tags.slugs())

    @patch('django.contrib.messages.api.add_message')
    @override_settings(PUBLIC_PROTO='http', PUBLIC_DOMAIN='readthedocs.org')
    def test_project_custom_resolver(self, add_message):

        with patch('readthedocs.projects.models.resolve') as resolve_func:
            publisher = Publisher.objects.create(
                name='Test Org',
                slug='testorg',
                metadata={},
                projects_metadata={},
                active=True
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
                active=True
            )

            project = Project.objects.create(
                name='my project',
                slug='myprojectslug',
                repo='https://github.com/testorg/myrepourl.git'
            )
            pub_project.projects.add(project)

            resolve_func.return_value = ItaliaResolver().resolve(
                project=project, version_slug=LATEST, language='en', private=False
            )
            self.assertEqual(project.get_docs_url(), '%s://%s/%s/%s/%s/en/%s/' % (
                settings.PUBLIC_PROTO, settings.PUBLIC_DOMAIN, publisher.slug,
                pub_project.slug, project.slug, LATEST
            ))

    @patch('django.contrib.messages.api.add_message')
    @patch('readthedocs.docsitalia.utils.get_subprojects')
    def test_project_sphinx_context_signal_works(self, get_subprojects, add_message):
        from readthedocs.doc_builder.signals import finalize_sphinx_context_data

        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            active=True
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
            active=True
        )

        project = Project.objects.create(
            name='my project',
            slug='myprojectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        pub_project.projects.add(project)
        remote = RemoteRepository.objects.create(
            full_name='remote repo name',
            html_url='https://github.com/testorg/myrepourl',
            project=project,
        )
        request = self.factory.get('/')
        request.user = self.user

        data = {}
        build_env = remote

        get_subprojects.return_value = ['sub1']
        finalize_sphinx_context_data.send(
            sender=self.__class__,
            build_env=build_env,
            data=data,
        )
        self.assertEqual(data, {'subprojects': [u'sub1']})

    def test_publisher_metadata_validation_parse_well_formed_metadata(self):
        data = validate_publisher_metadata(None, PUBLISHER_METADATA)
        self.assertTrue(data)

    def test_publisher_metadata_raise_value_error_on_empty_document(self):
        with self.assertRaises(ValueError):
            validate_publisher_metadata(None, '')

    def test_publisher_metadata_raise_value_error_without_publisher(self):
        with self.assertRaises(ValueError):
            validate_publisher_metadata(None, 'name: Ministero della Documentazione Pubblica')

    def test_projects_metadata_validation_parse_well_formed_metadata(self):
        org = RemoteOrganization(url='https://github.com/myorg')
        data = validate_projects_metadata(org, PROJECTS_METADATA)
        self.assertTrue(data)
        project = data['projects'][0]
        self.assertIn('repo_url', project)
        self.assertIn('slug', project)

    def test_projects_metadata_raise_value_error_on_empty_document(self):
        with self.assertRaises(ValueError):
            validate_projects_metadata(None, '')

    def test_projects_metadata_raise_value_error_without_projects(self):
        with self.assertRaises(ValueError):
            validate_projects_metadata(None, 'name: Progetto')

    def test_document_metadata_validation_parse_well_formed_metadata(self):
        data = validate_document_metadata(None, DOCUMENT_METADATA)
        self.assertTrue(data)

    def test_document_metadata_raise_value_error_on_empty_document(self):
        with self.assertRaises(ValueError):
            validate_document_metadata(None, '')

    def test_document_metadata_raise_value_error_without_document(self):
        with self.assertRaises(ValueError):
            validate_document_metadata(None, 'name: Documento')

    def test_project_root_is_served_by_docsitalia(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docsitalia/docsitalia_homepage.html')

    def test_metadata_webhook_github_updates_publisher_metadata(self):
        organization = RemoteOrganization.objects.create(
            slug='testorg',
            json='{}',
        )
        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            remote_organization=organization,
            active=True,
        )
        PublisherIntegration.objects.create(
            publisher=publisher,
            integration_type=PublisherIntegration.GITHUB_WEBHOOK
        )
        url = reverse('metadata_webhook_github', args=[publisher.slug])
        with requests_mock.Mocker() as rm:
            rm.get(
                'https://raw.githubusercontent.com/testorg/'
                'docs-italia-conf/master/publisher_settings.yml',
                text=PUBLISHER_METADATA)
            rm.get(
                'https://raw.githubusercontent.com/testorg/'
                'docs-italia-conf/master/projects_settings.yml',
                text=PROJECTS_METADATA)
            response = self.client.post(url, {'ref': 'refs/heads/master'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf-8'), {
            'build_triggered': True,
            'publisher': 'testorg',
            'versions': ['master']
        })

        publisher.refresh_from_db()
        self.assertNotEqual(publisher.metadata, {})
        self.assertNotEqual(publisher.projects_metadata, {})

    def test_metadata_webhook_calls_the_github_specific_one(self):
        from readthedocs.docsitalia.views.integrations import MetadataGitHubWebhookView
        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            active=True
        )
        integration = PublisherIntegration.objects.create(
            publisher=publisher,
            integration_type=PublisherIntegration.GITHUB_WEBHOOK
        )
        url = reverse('metadata_webhook', args=[publisher.slug, integration.pk])
        with patch.object(MetadataGitHubWebhookView, 'as_view') as view:
            view.return_value = lambda req, slug: Response()
            self.client.post(url, {})
        view.assert_called_once()

    def test_metadata_webhook_returns_404_if_integration_does_not_exist(self):
        url = reverse('metadata_webhook', args=['some-slug', 0])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 404)

    def test_on_webhook_github_signal_works(self):
        project = Project.objects.create(
            name='my project',
            slug='myprojectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        data = {
            'ref': 'master'
        }
        with requests_mock.Mocker() as rm:
            rm.get(
                'https://raw.githubusercontent.com/testorg/'
                'myrepourl/master/document_settings.yml',
                text=DOCUMENT_METADATA)
            webhook_github.send(Project, project=project, data=data, event='push')
        project.refresh_from_db()
        self.assertEqual(project.name, 'Documento Documentato Pubblicamente')
        self.assertEqual(project.description, 'Lorem ipsum dolor sit amet, consectetur\n')
        self.assertEqual(project.tags.count(), 1)
        self.assertIn('amazing-document', project.tags.slugs())

    def test_on_webhook_github_signal_ignores_not_push_events(self):
        webhook_github.send(Project, project=None, data=None, event='notpush')

    def test_on_webhook_github_signal_ignores_invalid_branches(self):
        webhook_github.send(Project, project=None, data={}, event='push')

        webhook_github.send(Project, project=None, data={'ref': 'notmaster'}, event='push')

    def test_we_use_docsitalia_builder_conf_template(self):
        template = get_template('doc_builder/conf.py.tmpl')
        self.assertIn('readthedocs/templates/doc_builder/conf.py.tmpl', template.origin.name)

    @pytest.mark.skipif(not IT_RESOLVER_IN_SETTINGS, reason='Require CLASS_OVERRIEDS in the settings file to work')
    @pytest.mark.itresolver
    @override_settings(PUBLIC_PROTO='http', PUBLIC_DOMAIN='readthedocs.org')
    def test_projects_by_tag_api_filter_tags(self):
        project = Project.objects.create(
            name='my project',
            slug='myprojectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        project.tags.add('lorem', 'ipsum')
        publisher = Publisher.objects.create(
            name='Test Org',
            slug='testorg',
            metadata={},
            projects_metadata={},
            active=True
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
            active=True
        )
        pub_project.projects.add(project)
        response = self.client.get(reverse('docsitalia-project-list'), {'tags': 'lorem, sicut'})
        self.assertEqual(len(response.data['results']), 1)
        self.assertJSONEqual(
            response.content.decode('utf-8'), {
              "count": 1,
              "next": None,
              "previous": None,
              "results": [
                {
                  "id": project.pk,
                  "name": "my project",
                  "slug": "myprojectslug",
                  "description": "",
                  "canonical_url": "http://readthedocs.org/testorg/testproject/myprojectslug/en/latest/",
                  "publisher": {
                    "canonical_url": "http://readthedocs.org/testorg",
                    "name": ""
                  },
                  "publisher_project": {
                    "canonical_url": "http://readthedocs.org/testorg/testproject",
                    "name": ""
                  }
                }
              ]
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_projects_by_tag_api_no_tags_provided(self):
        project = Project.objects.create(
            name='my project',
            slug='myprojectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        project.tags.add('lorem', 'ipsum')
        response = self.client.get(reverse('docsitalia-project-list'))
        self.assertTrue(response.data['results'])
        self.assertEqual(response.status_code, 200)

    def test_projects_by_tag_returns_only_data_that_matches_tags(self):
        project = Project.objects.create(
            name='my project',
            slug='myprojectslug',
            repo='https://github.com/testorg/myrepourl.git'
        )
        project.tags.add('lorem', 'ipsum')
        response = self.client.get(reverse('docsitalia-project-list'), {'tags': 'sicut, amet'})
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.status_code, 200)
